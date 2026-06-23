from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
import html
from .models import (
    Subject, Unit, Topic, Note, Mindmap, Flashcard, FlashcardReview,
    MCQQuestion, MCQAttempt, PYQQuestion, UserProgress, StudyPlan,
    StudyPlanItem, ChatMessage, StudySession, UserProfile,
    EmailVerification, PasswordReset, AITask
)
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .serializers import (
    SubjectSerializer, SubjectListSerializer, UnitSerializer, TopicSerializer,
    NoteSerializer, MindmapSerializer, FlashcardSerializer, FlashcardReviewSerializer,
    MCQQuestionSerializer, MCQQuestionListSerializer, MCQAttemptSerializer,
    PYQQuestionSerializer, UserProgressSerializer, StudyPlanSerializer,
    StudyPlanItemSerializer, ChatMessageSerializer, ChatRequestSerializer,
    UserSerializer, RegisterSerializer, LoginSerializer, StudySessionSerializer
)
from .ai_service import gemini_service
import logging
from datetime import timedelta


# === Security Helper Functions ===
def sanitize_text(text, max_length=10000):
    """Sanitize user input text to prevent XSS and limit length"""
    if not text:
        return ''
    if not isinstance(text, str):
        text = str(text)
    # Limit length
    text = text[:max_length]
    # HTML escape to prevent XSS
    text = html.escape(text)
    return text

logger = logging.getLogger(__name__)


def is_async_enabled():
    """Check if async task processing is enabled."""
    return getattr(settings, 'ENABLE_ASYNC_TASKS', False)


def run_task_async(func, *args, **kwargs):
    """
    Run a task asynchronously if enabled, otherwise run synchronously.
    Returns (is_async, task_id_or_result)
    """
    if is_async_enabled():
        try:
            from django_q.tasks import async_task
            task_id = async_task(func, *args, **kwargs)
            return True, task_id
        except ImportError:
            pass
    
    # Run synchronously
    result = func(*args, **kwargs)
    return False, result


def check_ai_usage(user):
    """
    Check if user can perform AI action.
    Returns (allowed, api_key, error_response)
    """
    try:
        profile = user.profile
    except:
        # Should exist due to signal, but just in case
        profile = UserProfile.objects.create(user=user)
    
    # Use encrypted API key getter
    api_key = profile.get_api_key()
    
    # If user has their own key, no limits
    if api_key:
        return True, api_key, None
    
    # Check daily limit
    today = timezone.now().date()
    if profile.last_usage_date != today:
        profile.daily_ai_usage_count = 0
        profile.last_usage_date = today
        profile.save()
    
    if profile.daily_ai_usage_count >= 3:
        return False, None, Response({
            'error': 'Daily AI limit reached (3 topics/day). Add your own Gemini API key in settings for unlimited access.',
            'limit_reached': True
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    return True, None, None

def increment_ai_usage(user):
    """Increment usage count if using system key"""
    try:
        profile = user.profile
        if not profile.get_api_key():
            profile.daily_ai_usage_count += 1
            profile.save()
    except:
        pass

def validate_positive_integer(value, field_name='value'):
    """Validate that a value is a positive integer"""
    try:
        val = int(value)
        if val < 0:
            raise ValidationError(f'{field_name} must be a positive integer')
        return val
    except (TypeError, ValueError):
        raise ValidationError(f'{field_name} must be a valid integer')

def validate_string_length(value, field_name, min_len=1, max_len=255):
    """Validate string length within bounds"""
    if not value or len(str(value)) < min_len:
        raise ValidationError(f'{field_name} must be at least {min_len} characters')
    if len(str(value)) > max_len:
        raise ValidationError(f'{field_name} must not exceed {max_len} characters')
    return str(value)


def update_token_usage(user, usage_data):
    """Update user's token usage stats"""
    if not usage_data or not user.is_authenticated:
        return
    
    try:
        profile = user.profile
        profile.total_input_tokens += usage_data.get('input', 0)
        profile.total_output_tokens += usage_data.get('output', 0)
        profile.save(update_fields=['total_input_tokens', 'total_output_tokens'])
    except Exception as e:
        logger.error(f"Failed to update token usage for user {user.username}: {e}")


def is_rate_limit_error(error_msg):
    """Detect if an error message corresponds to an AI rate limit/quota error"""
    if not error_msg:
        return False
    s = str(error_msg).lower()
    keywords = ['quota', 'rate limit', 'too many requests', '429', 'quota_exceeded', 'quota exceeded', 'rate-limited']
    return any(k in s for k in keywords)


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def _send_verification_email(self, user, verification):
        """Send verification email to user"""
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://padho-abhi.onrender.com')
        verify_url = f"{frontend_url}/verify-email?token={verification.token}"
        
        subject = "Verify your Padho Abhi account"
        message = f"""
Hello {user.username},

Welcome to Padho Abhi! 🎓

Please verify your email address by clicking the link below:

{verify_url}

This link will expire in 24 hours.

If you didn't create an account, you can safely ignore this email.

Best regards,
The Padho Abhi Team
        """
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #6366f1, #3b82f6); padding: 40px 20px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 28px; }}
        .header p {{ color: rgba(255,255,255,0.9); margin: 10px 0 0; }}
        .content {{ padding: 40px 30px; }}
        .content h2 {{ color: #1f2937; margin-top: 0; }}
        .content p {{ color: #4b5563; line-height: 1.6; }}
        .btn {{ display: inline-block; background: linear-gradient(135deg, #6366f1, #3b82f6); color: white; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
        .btn:hover {{ opacity: 0.9; }}
        .footer {{ background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
        .expire {{ background: #fef3c7; padding: 12px 20px; border-radius: 8px; color: #92400e; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Padho Abhi</h1>
            <p>AI-Powered Learning Platform</p>
        </div>
        <div class="content">
            <h2>Welcome, {user.username}! 👋</h2>
            <p>Thank you for signing up for Padho Abhi. To complete your registration and start your learning journey, please verify your email address.</p>
            <center><a href="{verify_url}" class="btn">Verify Email Address</a></center>
            <div class="expire">⏰ This link will expire in 24 hours</div>
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #6366f1;">{verify_url}</p>
        </div>
        <div class="footer">
            <p>If you didn't create this account, you can safely ignore this email.</p>
            <p>© 2026 Padho Abhi. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")
            return False

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            # Check if email already exists
            email = serializer.validated_data['email']
            if User.objects.filter(email=email).exists():
                return Response({
                    'error': 'An account with this email already exists.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = serializer.save()
            user.is_active = False  # Deactivate until email is verified
            user.save()
            
            # Create verification token
            verification = EmailVerification.objects.create(user=user)
            
            # Send verification email
            email_sent = self._send_verification_email(user, verification)
            
            if email_sent:
                return Response({
                    'message': 'Registration successful! Please check your email to verify your account.',
                    'email': user.email,
                    'requires_verification': True
                }, status=status.HTTP_201_CREATED)
            else:
                # If email fails, still create account but allow login
                user.is_active = True
                user.save()
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data,
                    'message': 'Account created. Email verification could not be sent.'
                }, status=status.HTTP_201_CREATED)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify_email(self, request):
        """Verify email with token"""
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Verification token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            verification = EmailVerification.objects.get(token=token)
        except EmailVerification.DoesNotExist:
            return Response({'error': 'Invalid verification token'}, status=status.HTTP_400_BAD_REQUEST)
        
        if verification.is_expired:
            return Response({'error': 'Verification link has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if verification.is_verified:
            return Response({'message': 'Email already verified. You can login now.'}, status=status.HTTP_200_OK)
        
        if verification.verify():
            auth_token, _ = Token.objects.get_or_create(user=verification.user)
            return Response({
                'message': 'Email verified successfully!',
                'token': auth_token.key,
                'user': UserSerializer(verification.user).data
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Verification failed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def resend_verification(self, request):
        """Resend verification email"""
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'No account found with this email'}, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_active:
            return Response({'message': 'Email already verified'}, status=status.HTTP_200_OK)
        
        # Invalidate old verifications and create new one
        EmailVerification.objects.filter(user=user, verified_at__isnull=True).delete()
        verification = EmailVerification.objects.create(user=user)
        
        if self._send_verification_email(user, verification):
            return Response({'message': 'Verification email sent!'}, status=status.HTTP_200_OK)
        
        return Response({'error': 'Failed to send email. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def forgot_password(self, request):
        """Request password reset"""
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists
            return Response({'message': 'If an account exists with this email, you will receive a password reset link.'}, status=status.HTTP_200_OK)
        
        # Create reset token
        reset = PasswordReset.objects.create(user=user)
        
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://padho-abhi.onrender.com')
        reset_url = f"{frontend_url}/reset-password?token={reset.token}"
        
        subject = "Reset your Padho Abhi password"
        message = f"""
Hello {user.username},

We received a request to reset your password. Click the link below to set a new password:

{reset_url}

This link will expire in 1 hour.

If you didn't request this, you can safely ignore this email.

Best regards,
The Padho Abhi Team
        """
        
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #6366f1, #3b82f6); padding: 40px 20px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 28px; }}
        .content {{ padding: 40px 30px; }}
        .content h2 {{ color: #1f2937; margin-top: 0; }}
        .content p {{ color: #4b5563; line-height: 1.6; }}
        .btn {{ display: inline-block; background: linear-gradient(135deg, #ef4444, #dc2626); color: white; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
        .footer {{ background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
        .expire {{ background: #fee2e2; padding: 12px 20px; border-radius: 8px; color: #991b1b; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Password Reset</h1>
        </div>
        <div class="content">
            <h2>Hello, {user.username}</h2>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <center><a href="{reset_url}" class="btn">Reset Password</a></center>
            <div class="expire">⏰ This link will expire in 1 hour</div>
            <p>If you didn't request this password reset, you can safely ignore this email.</p>
        </div>
        <div class="footer">
            <p>© 2026 Padho Abhi. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {e}")
        
        return Response({'message': 'If an account exists with this email, you will receive a password reset link.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        """Reset password with token"""
        token = request.data.get('token')
        new_password = request.data.get('password')
        
        if not token or not new_password:
            return Response({'error': 'Token and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 8:
            return Response({'error': 'Password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reset = PasswordReset.objects.get(token=token)
        except PasswordReset.DoesNotExist:
            return Response({'error': 'Invalid reset token'}, status=status.HTTP_400_BAD_REQUEST)
        
        if reset.is_expired:
            return Response({'error': 'Reset link has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if reset.is_used:
            return Response({'error': 'This reset link has already been used.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset the password
        reset.user.set_password(new_password)
        reset.user.save()
        reset.use()
        
        return Response({'message': 'Password reset successfully! You can now login with your new password.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user:
                if not user.is_active:
                    return Response({
                        'error': 'Please verify your email before logging in.',
                        'requires_verification': True,
                        'email': user.email
                    }, status=status.HTTP_403_FORBIDDEN)
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data
                })
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        data = UserSerializer(request.user).data
        try:
            profile = request.user.profile
            data['has_api_key'] = profile.has_api_key()
            data['daily_usage'] = profile.daily_ai_usage_count
            # Never return the actual API key - only masked version if exists
            api_key = profile.get_api_key()
            if api_key:
                # Mask API key: show first 4 and last 4 characters
                data['api_key_masked'] = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
            data['total_input_tokens'] = profile.total_input_tokens
            data['total_output_tokens'] = profile.total_output_tokens
            data['estimated_cost'] = float(profile.estimated_cost)
        except:
            data['has_api_key'] = False
            data['daily_usage'] = 0
            data['total_input_tokens'] = 0
            data['total_output_tokens'] = 0
            data['estimated_cost'] = 0.0
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def update_api_key(self, request):
        """Update user's Gemini API key (encrypted)"""
        api_key = request.data.get('api_key', '').strip()
        try:
            profile = request.user.profile
        except:
            profile = UserProfile.objects.create(user=request.user)
        
        # Use encrypted setter
        profile.set_api_key(api_key if api_key else None)
        profile.save()
        
        return Response({
            'status': 'success',
            'has_api_key': profile.has_api_key()
        })


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Subject.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SubjectListSerializer
        return SubjectSerializer
    
    @action(detail=False, methods=['post'])
    def upload_syllabus(self, request):
        """Upload and parse a syllabus to create subject, units, and topics"""
        # Check usage limit
        allowed, api_key, error_response = check_ai_usage(request.user)
        if not allowed:
            return error_response

        syllabus_text = request.data.get('syllabus_text', '')
        subject_name = request.data.get('subject_name', '')
        
        if not syllabus_text or not subject_name:
            return Response({
                'error': 'Both syllabus_text and subject_name are required'
            }, status=400)
        
        # Parse syllabus using AI
        parsed = gemini_service.parse_syllabus(syllabus_text, subject_name, api_key=api_key)

        if 'error' in parsed:
            err = parsed['error']
            if is_rate_limit_error(err):
                logger.warning('AI quota exceeded during syllabus upload: %s', err)
                return Response({'error': 'AI quota exceeded: ' + str(err)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            return Response({'error': parsed['error']}, status=500)
        
        # Increment usage if successful
        increment_ai_usage(request.user)
        update_token_usage(request.user, parsed.get('usage'))
        
        # Create subject
        subject, created = Subject.objects.update_or_create(
            name=parsed.get('subject_name', subject_name),
            user=request.user,
            defaults={
                'code': parsed.get('subject_code', ''),
                'description': parsed.get('description', '')
            }
        )
        
        # If subject exists, delete old units and topics
        if not created:
            subject.units.all().delete()
        
        # Create units and topics
        units_created = 0
        topics_created = 0
        
        for unit_data in parsed.get('units', []):
            unit = Unit.objects.create(
                subject=subject,
                unit_number=unit_data.get('unit_number', units_created + 1),
                name=unit_data.get('name', f'Unit {units_created + 1}'),
                description=unit_data.get('description', '')
            )
            units_created += 1
            
            for order, topic_name in enumerate(unit_data.get('topics', []), start=1):
                # Handle both string topics and dict topics (in case AI returns wrong format)
                if isinstance(topic_name, dict):
                    # If it's a dict, try to get 'title' or 'name' field
                    topic_name = topic_name.get('title', topic_name.get('name', str(topic_name)))
                
                Topic.objects.create(
                    unit=unit,
                    name=str(topic_name),
                    order=order
                )
                topics_created += 1
        
        return Response({
            'status': 'success',
            'subject': SubjectSerializer(subject).data,
            'summary': {
                'units_created': units_created,
                'topics_created': topics_created
            }
        })
    
    @action(detail=True, methods=['delete'])
    def delete_with_content(self, request, pk=None):
        """Delete subject and all related content"""
        subject = self.get_object()
        subject_name = subject.name
        subject.delete()
        return Response({
            'status': 'success',
            'message': f'Subject "{subject_name}" and all related content deleted'
        })


class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    
    def get_queryset(self):
        queryset = Unit.objects.filter(subject__user=self.request.user)
        subject_id = self.request.query_params.get('subject', None)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        return queryset


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    
    def get_queryset(self):
        queryset = Topic.objects.filter(unit__subject__user=self.request.user)
        unit_id = self.request.query_params.get('unit', None)
        subject_id = self.request.query_params.get('subject', None)
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        if subject_id:
            queryset = queryset.filter(unit__subject_id=subject_id)
        return queryset
    
    @action(detail=True, methods=['post'])
    def generate_content(self, request, pk=None):
        """Generate all content (notes, mindmap, flashcards, MCQs) for a topic"""
        # Check usage limit
        allowed, api_key, error_response = check_ai_usage(request.user)
        if not allowed:
            return error_response

        topic = self.get_object()
        subject_name = topic.unit.subject.name
        
        # Check if async mode requested
        use_async = request.data.get('async', False) and is_async_enabled()
        
        if use_async:
            # Create pending task record
            task, _ = AITask.objects.update_or_create(
                topic=topic,
                user=request.user,
                task_type='generate_all',
                defaults={'status': 'pending'}
            )
            
            # Run in background
            from .tasks import generate_content_task
            is_async, task_id = run_task_async(
                generate_content_task,
                topic.id,
                request.user.id,
                api_key
            )
            
            if is_async:
                return Response({
                    'status': 'processing',
                    'message': 'Content generation started in background',
                    'task_id': str(task.id),
                    'poll_url': f'/api/topics/{topic.id}/task_status/'
                }, status=status.HTTP_202_ACCEPTED)
        
        # Synchronous generation (original behavior)
        content = gemini_service.generate_all_content(topic.name, subject_name, api_key=api_key)

        # Check for errors in content (e.g., AI rate limits or parsing failures)
        errors = []
        if 'notes' in content and isinstance(content['notes'], dict) and 'error' in content['notes']:
            errors.append(('notes', content['notes']['error']))
        if 'mindmap' in content and isinstance(content['mindmap'], dict) and 'error' in content['mindmap']:
            errors.append(('mindmap', content['mindmap']['error']))
        if 'flashcards' in content and isinstance(content['flashcards'], dict) and 'error' in content['flashcards']:
            errors.append(('flashcards', content['flashcards']['error']))
        if 'mcqs' in content and isinstance(content['mcqs'], dict) and 'error' in content['mcqs']:
            errors.append(('mcqs', content['mcqs']['error']))
        # If we find rate-limit errors, return 429 immediately
        for part, err in errors:
            if is_rate_limit_error(err):
                return Response({'error': 'AI quota exceeded: ' + str(err)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        if errors:
            # Return an internal server error with details about what failed
            logger.error('AI generation failed for parts: %s', errors)
            return Response({'error': 'AI generation failed', 'details': errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Increment usage if successful
        increment_ai_usage(request.user)
        update_token_usage(request.user, content.get('usage'))

        # Save notes
        if 'notes' in content and 'error' not in content['notes']:
            Note.objects.update_or_create(
                topic=topic,
                defaults={
                    'summary': content['notes'].get('summary', ''),
                    'detailed_content': content['notes'].get('detailed_content', ''),
                    'analogies': content['notes'].get('analogies', []),
                    'diagram_description': content['notes'].get('diagram_description', '')
                }
            )
        
        # Save mindmap
        if 'mindmap' in content and 'error' not in content['mindmap']:
            Mindmap.objects.update_or_create(
                topic=topic,
                defaults={'json_data': content['mindmap']}
            )
        
        # Save flashcards
        if 'flashcards' in content and content['flashcards']:
            flashcards_to_create = [
                Flashcard(
                    topic=topic,
                    front_text=fc.get('front', ''),
                    back_text=fc.get('back', '')
                )
                for fc in content['flashcards']
            ]
            if flashcards_to_create:
                Flashcard.objects.bulk_create(flashcards_to_create)
        
        # Save MCQs
        if 'mcqs' in content and content['mcqs']:
            mcqs_to_create = []
            for mcq in content['mcqs']:
                options = mcq.get('options', {})
                mcqs_to_create.append(
                    MCQQuestion(
                        topic=topic,
                        question_text=mcq.get('question', ''),
                        option_a=options.get('a', ''),
                        option_b=options.get('b', ''),
                        option_c=options.get('c', ''),
                        option_d=options.get('d', ''),
                        correct_option=mcq.get('correct', 'a'),
                        explanation=mcq.get('explanation', ''),
                        difficulty=mcq.get('difficulty', 'medium')
                    )
                )
            if mcqs_to_create:
                MCQQuestion.objects.bulk_create(mcqs_to_create)
        
        return Response({
            'status': 'success',
            'message': f'Content generated for {topic.name}',
            'content_summary': {
                'notes': 'notes' in content,
                'mindmap': 'mindmap' in content,
                'flashcards': len(content.get('flashcards', [])),
                'mcqs': len(content.get('mcqs', []))
            }
        })

    @action(detail=True, methods=['get'])
    def task_status(self, request, pk=None):
        """Check the status of a background AI task"""
        topic = self.get_object()
        task_type = request.query_params.get('type', 'generate_all')
        
        try:
            task = AITask.objects.filter(
                topic=topic,
                user=request.user,
                task_type=task_type
            ).latest('created_at')
            
            return Response({
                'status': task.status,
                'created_at': task.created_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at,
                'error_message': task.error_message,
                'result': task.result
            })
        except AITask.DoesNotExist:
            return Response({
                'status': 'not_found',
                'message': 'No task found for this topic'
            }, status=status.HTTP_404_NOT_FOUND)


class NoteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    def get_queryset(self):
        return Note.objects.filter(topic__unit__subject__user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_topic(self, request):
        topic_id = request.query_params.get('topic_id')
        refresh = request.query_params.get('refresh') == 'true'
        if not topic_id:
            return Response({'error': 'topic_id is required'}, status=400)
        
        topic = get_object_or_404(Topic, pk=topic_id)
        
        # Check if notes exist, if not generate them
        try:
            note = topic.note
            if refresh:
                note.delete()
                raise Note.DoesNotExist
        except Note.DoesNotExist:
            # Check usage limit
            allowed, api_key, error_response = check_ai_usage(request.user)
            if not allowed:
                return error_response

            # Generate notes
            subject_name = topic.unit.subject.name
            notes_data = gemini_service.generate_notes(topic.name, subject_name, api_key=api_key)

            if 'error' in notes_data:
                err = notes_data['error']
                if is_rate_limit_error(err):
                    logger.warning('AI quota exceeded generating notes: %s', err)
                    return Response({'error': 'AI quota exceeded: ' + str(err)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
                return Response({'error': notes_data['error']}, status=500)
            
            # Increment usage
            increment_ai_usage(request.user)
            update_token_usage(request.user, notes_data.get('usage'))

            note = Note.objects.create(
                topic=topic,
                summary=notes_data.get('summary', ''),
                detailed_content=notes_data.get('detailed_content', ''),
                analogies=notes_data.get('analogies', []),
                diagram_description=notes_data.get('diagram_description', '')
            )
        
        serializer = NoteSerializer(note)
        return Response(serializer.data)


    
    def get_queryset(self):
        return Mindmap.objects.filter(topic__unit__subject__user=self.request.user)
class MindmapViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Mindmap.objects.all()
    serializer_class = MindmapSerializer
    
    @action(detail=False, methods=['get'])
    def by_topic(self, request):
        topic_id = request.query_params.get('topic_id')
        refresh = request.query_params.get('refresh') == 'true'
        if not topic_id:
            return Response({'error': 'topic_id is required'}, status=400)
        
        topic = get_object_or_404(Topic, pk=topic_id)
        
        # Check if mindmap exists, if not generate it
        try:
            mindmap = topic.mindmap
            if refresh:
                mindmap.delete()
                raise Mindmap.DoesNotExist
        except Mindmap.DoesNotExist:
            # Check usage limit
            allowed, api_key, error_response = check_ai_usage(request.user)
            if not allowed:
                return error_response

            # Generate mindmap
            subject_name = topic.unit.subject.name
            mindmap_data = gemini_service.generate_mindmap(topic.name, subject_name, api_key=api_key)

            if 'error' in mindmap_data:
                err = mindmap_data['error']
                if is_rate_limit_error(err):
                    logger.warning('AI quota exceeded generating mindmap: %s', err)
                    return Response({'error': 'AI quota exceeded: ' + str(err)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
                return Response({'error': mindmap_data['error']}, status=500)
            
            # Increment usage
            increment_ai_usage(request.user)
            update_token_usage(request.user, mindmap_data.get('usage'))
            
            # Remove usage metadata before saving
            if 'usage' in mindmap_data:
                del mindmap_data['usage']

            mindmap = Mindmap.objects.create(
                topic=topic,
                json_data=mindmap_data
            )
        
        serializer = MindmapSerializer(mindmap)
        return Response(serializer.data)


class FlashcardViewSet(viewsets.ModelViewSet):
    queryset = Flashcard.objects.all()
    serializer_class = FlashcardSerializer
    
    def get_queryset(self):
        queryset = Flashcard.objects.filter(topic__unit__subject__user=self.request.user)
        topic_id = self.request.query_params.get('topic_id')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_topic(self, request):
        topic_id = request.query_params.get('topic_id')
        refresh = request.query_params.get('refresh') == 'true'
        if not topic_id:
            return Response({'error': 'topic_id is required'}, status=400)
        
        topic = get_object_or_404(Topic, pk=topic_id)
        flashcards = topic.flashcards.all()
        
        # If no flashcards exist or refresh requested, generate them
        if not flashcards.exists() or refresh:
            if refresh:
                flashcards.delete()
            
            # Check usage limit
            allowed, api_key, error_response = check_ai_usage(request.user)
            if not allowed:
                return error_response

            # Get notes content if available
            notes_content = ""
            try:
                notes_content = topic.note.detailed_content or topic.note.summary
            except Note.DoesNotExist:
                pass
            
            flashcards_data = gemini_service.generate_flashcards(topic.name, notes_content, api_key=api_key)

            if 'error' in flashcards_data:
                err = flashcards_data['error']
                if is_rate_limit_error(err):
                    logger.warning('AI quota exceeded generating flashcards: %s', err)
                    return Response({'error': 'AI quota exceeded: ' + str(err)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
                return Response({'error': err}, status=500)

            # Increment usage
            increment_ai_usage(request.user)
            update_token_usage(request.user, flashcards_data.get('usage'))

            flashcards_to_create = [
                Flashcard(
                    topic=topic,
                    front_text=fc.get('front', ''),
                    back_text=fc.get('back', '')
                )
                for fc in flashcards_data.get('flashcards', [])
            ]
            if flashcards_to_create:
                Flashcard.objects.bulk_create(flashcards_to_create)
            
            flashcards = topic.flashcards.all()
        
        serializer = FlashcardSerializer(flashcards, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Record a flashcard review for spaced repetition"""
        flashcard = self.get_object()
        quality = request.data.get('quality', 0)  # 0-5
        
        review, created = FlashcardReview.objects.get_or_create(
            user=request.user,
            flashcard=flashcard
        )
        review.update_next_due(quality)
        
        return Response({
            'status': 'success',
            'next_due_at': review.next_due_at
        })


class MCQViewSet(viewsets.ModelViewSet):
    queryset = MCQQuestion.objects.all()
    serializer_class = MCQQuestionSerializer
    
    def get_queryset(self):
        queryset = MCQQuestion.objects.filter(topic__unit__subject__user=self.request.user)
        topic_id = self.request.query_params.get('topic_id')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_topic(self, request):
        topic_id = request.query_params.get('topic_id')
        refresh = request.query_params.get('refresh') == 'true'
        if not topic_id:
            return Response({'error': 'topic_id is required'}, status=400)
        
        topic = get_object_or_404(Topic, pk=topic_id)
        mcqs = topic.mcqs.all()
        
        # If no MCQs exist or refresh requested, generate them
        if not mcqs.exists() or refresh:
            if refresh:
                mcqs.delete()
            
            # Check usage limit
            allowed, api_key, error_response = check_ai_usage(request.user)
            if not allowed:
                return error_response

            notes_content = ""
            try:
                notes_content = topic.note.detailed_content or topic.note.summary
            except Note.DoesNotExist:
                pass
            
            mcqs_data = gemini_service.generate_mcqs(topic.name, notes_content, api_key=api_key)

            if 'error' in mcqs_data:
                err = mcqs_data['error']
                if is_rate_limit_error(err):
                    logger.warning('AI quota exceeded generating mcqs: %s', err)
                    return Response({'error': 'AI quota exceeded: ' + str(err)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
                return Response({'error': err}, status=500)

            # Increment usage
            increment_ai_usage(request.user)
            update_token_usage(request.user, mcqs_data.get('usage'))

            mcqs_to_create = []
            for mcq in mcqs_data.get('mcqs', []):
                options = mcq.get('options', {})
                mcqs_to_create.append(
                    MCQQuestion(
                        topic=topic,
                        question_text=mcq.get('question', ''),
                        option_a=options.get('a', ''),
                        option_b=options.get('b', ''),
                        option_c=options.get('c', ''),
                        option_d=options.get('d', ''),
                        correct_option=mcq.get('correct', 'a'),
                        explanation=mcq.get('explanation', ''),
                        difficulty=mcq.get('difficulty', 'medium')
                    )
                )
            if mcqs_to_create:
                MCQQuestion.objects.bulk_create(mcqs_to_create)
            
            mcqs = topic.mcqs.all()
        
        # Return without answers for quiz mode
        hide_answers = request.query_params.get('quiz_mode', 'false').lower() == 'true'
        if hide_answers:
            serializer = MCQQuestionListSerializer(mcqs, many=True)
        else:
            serializer = MCQQuestionSerializer(mcqs, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def submit_answer(self, request, pk=None):
        """Submit an answer for an MCQ"""
        mcq = self.get_object()
        selected_option = request.data.get('selected_option', '').lower()
        
        if selected_option not in ['a', 'b', 'c', 'd']:
            return Response({'error': 'Invalid option'}, status=400)
        
        is_correct = selected_option == mcq.correct_option
        
        MCQAttempt.objects.create(
            user=request.user,
            mcq=mcq,
            selected_option=selected_option,
            is_correct=is_correct
        )
        
        # Update progress
        progress, _ = UserProgress.objects.get_or_create(user=request.user, topic=mcq.topic)
        progress.mcqs_attempted += 1
        if is_correct:
            progress.mcqs_correct += 1
        progress.last_studied_at = timezone.now()
        progress.save()
        
        return Response({
            'is_correct': is_correct,
            'correct_option': mcq.correct_option,
            'explanation': mcq.explanation
        })


class PYQViewSet(viewsets.ModelViewSet):
    queryset = PYQQuestion.objects.all()
    serializer_class = PYQQuestionSerializer
    
    def get_queryset(self):
        queryset = PYQQuestion.objects.filter(subject__user=self.request.user)
        subject_id = self.request.query_params.get('subject_id')
        topic_id = self.request.query_params.get('topic_id')
        year = self.request.query_params.get('year')
        
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        if year:
            queryset = queryset.filter(year=year)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def analysis(self, request):
        """Get PYQ analysis for a subject"""
        subject_id = request.query_params.get('subject_id')
        if not subject_id:
            return Response({'error': 'subject_id is required'}, status=400)
        
        # Topic-wise analysis
        topic_stats = PYQQuestion.objects.filter(
            subject_id=subject_id,
            topic__isnull=False
        ).values('topic__id', 'topic__name').annotate(
            total_questions=Count('id'),
            total_marks=Sum('marks'),
            years_appeared=Count('year', distinct=True)
        ).order_by('-total_marks')
        
        # Year-wise distribution
        year_stats = PYQQuestion.objects.filter(
            subject_id=subject_id
        ).values('year').annotate(
            question_count=Count('id'),
            total_marks=Sum('marks')
        ).order_by('-year')
        
        return Response({
            'topic_analysis': list(topic_stats),
            'year_distribution': list(year_stats)
        })
    
    @action(detail=False, methods=['post'])
    def tag_questions(self, request):
        """Auto-tag untagged PYQs to topics using AI"""
        subject_id = request.data.get('subject_id')
        if not subject_id:
            return Response({'error': 'subject_id is required'}, status=400)
        
        subject = get_object_or_404(Subject, pk=subject_id)
        untagged_pyqs = PYQQuestion.objects.filter(subject=subject, is_tagged=False)
        
        # Get all topics for this subject
        topics = Topic.objects.filter(unit__subject=subject)
        topic_names = [t.name for t in topics]
        topic_map = {t.name.lower(): t for t in topics}
        
        tagged_count = 0
        for pyq in untagged_pyqs:
            result = gemini_service.tag_pyq_to_topic(pyq.question_text, topic_names)
            
            if 'error' in result:
                continue

            update_token_usage(request.user, result.get('usage'))
            topic_name = result.get('topic')

            if topic_name:
                topic_name_lower = topic_name.lower().strip()
                if topic_name_lower in topic_map:
                    pyq.topic = topic_map[topic_name_lower]
                    pyq.is_tagged = True
                    pyq.save()
                    tagged_count += 1
        
        return Response({
            'status': 'success',
            'tagged_count': tagged_count,
            'total_untagged': untagged_pyqs.count()
        })


class UserProgressViewSet(viewsets.ModelViewSet):
    queryset = UserProgress.objects.all()
    serializer_class = UserProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = UserProgress.objects.filter(user=self.request.user)
        subject_id = self.request.query_params.get('subject_id')
        
        if subject_id:
            queryset = queryset.filter(topic__unit__subject_id=subject_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get overall progress dashboard"""
        subject_id = request.query_params.get('subject_id')
        
        # ⚡ Bolt: Use select_related to prevent N+1 queries when accessing p.topic.name
        progress_qs = UserProgress.objects.filter(user=request.user).select_related('topic')
        if subject_id:
            progress_qs = progress_qs.filter(topic__unit__subject_id=subject_id)
            total_topics = Topic.objects.filter(unit__subject_id=subject_id).count()
        else:
            total_topics = Topic.objects.count()
        
        # Calculate stats
        progress_list = list(progress_qs)
        completed_topics = sum(1 for p in progress_list if p.is_completed)
        
        # Calculate average completion percentage across all topics
        total_completion_sum = sum(p.completion_percentage for p in progress_list)
        avg_completion = (total_completion_sum / total_topics) if total_topics > 0 else 0
        
        total_mcqs_attempted = sum(p.mcqs_attempted for p in progress_list)
        total_mcqs_correct = sum(p.mcqs_correct for p in progress_list)
        overall_accuracy = (total_mcqs_correct / total_mcqs_attempted * 100) if total_mcqs_attempted > 0 else 0
        
        weak_topics = [p.topic.name for p in progress_list if p.strength_level == 'weak' and p.mcqs_attempted >= 5]
        strong_topics = [p.topic.name for p in progress_list if p.strength_level == 'strong']
        
        return Response({
            'total_topics': total_topics,
            'completed_topics': completed_topics,
            'completion_percentage': avg_completion,
            'overall_mcq_accuracy': overall_accuracy,
            'weak_topics': weak_topics,
            'strong_topics': strong_topics
        })
    
    @action(detail=False, methods=['post'])
    def update_activity(self, request):
        """Update user's activity on a topic"""
        topic_id = request.data.get('topic_id')
        activity_type = request.data.get('activity_type')  # mindmap, notes, flashcard, time
        duration = request.data.get('duration', 0) # in seconds
        
        if not topic_id:
            return Response({'error': 'topic_id required'}, status=400)
        
        topic = get_object_or_404(Topic, pk=topic_id)
        progress, _ = UserProgress.objects.get_or_create(user=request.user, topic=topic)
        
        if activity_type == 'mindmap':
            progress.mindmap_viewed = True
        elif activity_type == 'notes':
            progress.notes_read = True
        elif activity_type == 'flashcard':
            progress.flashcards_completed += 1
        elif activity_type == 'time':
            progress.total_study_time += int(duration)
        
        progress.last_studied_at = timezone.now()
        progress.save()
        
        return Response(UserProgressSerializer(progress).data)
    
    @action(detail=False, methods=['post'])
    def mark_complete(self, request):
        """Mark a topic as completed (user confirmed)"""
        topic_id = request.data.get('topic_id')
        confirm = request.data.get('confirm', False)
        
        if not topic_id:
            return Response({'error': 'topic_id required'}, status=400)
        
        topic = get_object_or_404(Topic, pk=topic_id)
        progress, _ = UserProgress.objects.get_or_create(user=request.user, topic=topic)
        
        # Check criteria
        warnings = []
        if progress.total_study_time < 1500: # 25 minutes
            warnings.append(f"You have only spent {progress.total_study_time // 60} minutes on this topic. Recommended time is 25 minutes.")
        
        if progress.mcq_accuracy < 60 and progress.mcqs_attempted > 0:
             warnings.append(f"Your MCQ accuracy is {progress.mcq_accuracy:.1f}%. Recommended is 60%.")
        
        if warnings and not confirm:
            return Response({
                'status': 'warning',
                'warnings': warnings,
                'message': 'Are you sure you want to mark this as complete?'
            })

        progress.mark_complete()
        
        return Response({
            'status': 'success',
            'message': f'Topic "{topic.name}" marked as complete',
            'progress': UserProgressSerializer(progress).data
        })
    
    @action(detail=False, methods=['get'])
    def by_topic(self, request):
        """Get progress for a specific topic"""
        topic_id = request.query_params.get('topic_id')
        
        if not topic_id:
            return Response({'error': 'topic_id required'}, status=400)
        
        topic = get_object_or_404(Topic, pk=topic_id)
        progress, _ = UserProgress.objects.get_or_create(user=request.user, topic=topic)
        
        return Response(UserProgressSerializer(progress).data)


class ChatView(APIView):
    """Doubt chatbot endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Check usage limit
        allowed, api_key, error_response = check_ai_usage(request.user)
        if not allowed:
            return error_response

        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        topic_id = serializer.validated_data['topic_id']
        user_message = serializer.validated_data['message']
        
        topic = get_object_or_404(Topic, pk=topic_id)
        
        # Get notes content for context
        notes_content = ""
        try:
            notes_content = topic.note.detailed_content or topic.note.summary
        except Note.DoesNotExist:
            # Generate notes first
            subject_name = topic.unit.subject.name
            notes_data = gemini_service.generate_notes(topic.name, subject_name, api_key=api_key)
            if 'error' not in notes_data:
                Note.objects.create(
                    topic=topic,
                    summary=notes_data.get('summary', ''),
                    detailed_content=notes_data.get('detailed_content', ''),
                    analogies=notes_data.get('analogies', []),
                    diagram_description=notes_data.get('diagram_description', '')
                )
                notes_content = notes_data.get('detailed_content', notes_data.get('summary', ''))
        
        # Get AI response
        result = gemini_service.answer_doubt(user_message, topic.name, notes_content, api_key=api_key)
        
        if 'error' in result:
            err = result['error']
            if is_rate_limit_error(err):
                return Response({'error': err}, status=429)
            return Response({'error': err}, status=500)

        update_token_usage(request.user, result.get('usage'))
        ai_response = result.get('answer', '')
        
        # Increment usage
        increment_ai_usage(request.user)
        
        # Save chat message
        chat_message = ChatMessage.objects.create(
            user=request.user,
            topic=topic,
            user_message=user_message,
            ai_response=ai_response
        )
        
        return Response(ChatMessageSerializer(chat_message).data)


class StudySessionViewSet(viewsets.ModelViewSet):
    """Track study sessions for timer functionality"""
    queryset = StudySession.objects.all()
    serializer_class = StudySessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudySession.objects.filter(user=self.request.user).order_by('-started_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get currently active (non-ended) session"""
        session = StudySession.objects.filter(user=request.user, ended_at__isnull=True).first()
        if session:
            return Response(StudySessionSerializer(session).data)
        return Response({'active': None})

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a study session and compute duration"""
        session = self.get_object()
        if session.ended_at:
            return Response({'error': 'Session already ended'}, status=400)
        session.end()
        
        # Update user progress for the topic
        progress, _ = UserProgress.objects.get_or_create(user=request.user, topic=session.topic)
        progress.last_studied_at = timezone.now()
        progress.total_study_time += session.duration_seconds
        progress.save()
        
        return Response(StudySessionSerializer(session).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get total study time stats"""
        sessions = StudySession.objects.filter(user=request.user, ended_at__isnull=False)
        total_seconds = sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0
        
        topic_id = request.query_params.get('topic_id')
        if topic_id:
            topic_sessions = sessions.filter(topic_id=topic_id)
            topic_seconds = topic_sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0
        else:
            topic_seconds = 0
        
        return Response({
            'total_study_time_seconds': total_seconds,
            'total_study_time_minutes': total_seconds // 60,
            'topic_study_time_seconds': topic_seconds,
            'topic_study_time_minutes': topic_seconds // 60
        })


class StudyPlanViewSet(viewsets.ModelViewSet):
    queryset = StudyPlan.objects.all()
    serializer_class = StudyPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a study plan"""
        subject_id = request.data.get('subject_id')
        exam_date = request.data.get('exam_date')
        hours_per_day = request.data.get('hours_per_day', 2.0)
        
        if not subject_id or not exam_date:
            return Response({'error': 'subject_id and exam_date required'}, status=400)
        
        from datetime import datetime
        
        subject = get_object_or_404(Subject, pk=subject_id)
        
        # Parse exam date
        exam_date = datetime.strptime(exam_date, '%Y-%m-%d').date()
        today = timezone.now().date()
        days_available = (exam_date - today).days
        
        if days_available <= 0:
            return Response({'error': 'Exam date must be in the future'}, status=400)
        
        # Create study plan
        plan = StudyPlan.objects.create(
            user=request.user,
            subject=subject,
            exam_date=exam_date,
            hours_per_day=hours_per_day
        )
        
        # Get all topics
        topics = list(Topic.objects.filter(unit__subject=subject).order_by('unit__unit_number', 'order'))
        
        # Distribute topics across days
        topics_per_day = max(1, len(topics) // days_available)
        
        current_date = today
        for i, topic in enumerate(topics):
            if i > 0 and i % topics_per_day == 0:
                current_date += timedelta(days=1)
            
            if current_date >= exam_date:
                current_date = exam_date - timedelta(days=1)
            
            StudyPlanItem.objects.create(
                plan=plan,
                topic=topic,
                scheduled_date=current_date
            )
        
        return Response(StudyPlanSerializer(plan).data)