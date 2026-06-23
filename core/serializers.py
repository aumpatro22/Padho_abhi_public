from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    Subject, Unit, Topic, Note, Mindmap, Flashcard, FlashcardReview,
    MCQQuestion, MCQAttempt, PYQQuestion, UserProgress, StudyPlan,
    StudyPlanItem, ChatMessage
)

from .models import StudySession


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class TopicSerializer(serializers.ModelSerializer):
    has_notes = serializers.SerializerMethodField()
    has_mindmap = serializers.SerializerMethodField()
    flashcard_count = serializers.SerializerMethodField()
    mcq_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = ['id', 'name', 'description', 'order', 'has_notes', 
                  'has_mindmap', 'flashcard_count', 'mcq_count']
    
    def get_has_notes(self, obj):
        return hasattr(obj, 'note')
    
    def get_has_mindmap(self, obj):
        return hasattr(obj, 'mindmap')
    
    def get_flashcard_count(self, obj):
        if hasattr(obj, 'flashcard_count_annotated'):
            return obj.flashcard_count_annotated
        return obj.flashcards.count()
    
    def get_mcq_count(self, obj):
        if hasattr(obj, 'mcq_count_annotated'):
            return obj.mcq_count_annotated
        return obj.mcqs.count()


class UnitSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)
    topic_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = ['id', 'name', 'unit_number', 'description', 'topics', 'topic_count']
    
    def get_topic_count(self, obj):
        if hasattr(obj, 'topic_count'):
            return obj.topic_count
        return obj.topics.count()


class SubjectSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)
    unit_count = serializers.SerializerMethodField()
    topic_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'description', 'units', 'unit_count', 'topic_count']
    
    def get_unit_count(self, obj):
        return obj.units.count()
    
    def get_topic_count(self, obj):
        return Topic.objects.filter(unit__subject=obj).count()


class SubjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing subjects"""
    unit_count = serializers.SerializerMethodField()
    topic_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'description', 'unit_count', 'topic_count']
    
    def get_unit_count(self, obj):
        return obj.units.count()
    
    def get_topic_count(self, obj):
        return Topic.objects.filter(unit__subject=obj).count()


class NoteSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    
    class Meta:
        model = Note
        fields = ['id', 'topic', 'topic_name', 'summary', 'detailed_content', 
                  'analogies', 'diagram_description', 'created_at', 'updated_at']


class MindmapSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    
    class Meta:
        model = Mindmap
        fields = ['id', 'topic', 'topic_name', 'json_data', 'created_at']


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ['id', 'topic', 'front_text', 'back_text', 'difficulty', 'created_at']


class FlashcardReviewSerializer(serializers.ModelSerializer):
    flashcard = FlashcardSerializer(read_only=True)
    
    class Meta:
        model = FlashcardReview
        fields = ['id', 'flashcard', 'last_reviewed_at', 'quality', 'next_due_at']


class MCQQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCQQuestion
        fields = ['id', 'topic', 'question_text', 'option_a', 'option_b', 
                  'option_c', 'option_d', 'correct_option', 'explanation', 
                  'difficulty', 'created_at']


class MCQQuestionListSerializer(serializers.ModelSerializer):
    """Serializer without answer for quiz mode"""
    class Meta:
        model = MCQQuestion
        fields = ['id', 'topic', 'question_text', 'option_a', 'option_b', 
                  'option_c', 'option_d', 'difficulty']


class MCQAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCQAttempt
        fields = ['id', 'mcq', 'selected_option', 'is_correct', 'attempted_at']
        read_only_fields = ['is_correct']


class PYQQuestionSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    
    class Meta:
        model = PYQQuestion
        fields = ['id', 'subject', 'topic', 'topic_name', 'year', 'exam_type', 
                  'question_text', 'marks', 'is_tagged']


class UserProgressSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    mcq_accuracy = serializers.FloatField(read_only=True)
    completion_percentage = serializers.IntegerField(read_only=True)
    strength_level = serializers.CharField(read_only=True)
    
    class Meta:
        model = UserProgress
        fields = ['id', 'topic', 'topic_name', 'mindmap_viewed', 'notes_read',
                  'flashcards_completed', 'mcqs_attempted', 'mcqs_correct',
                  'is_completed', 'completed_at', 'total_study_time',
                  'last_studied_at', 'mcq_accuracy', 'completion_percentage', 
                  'strength_level']


class StudyPlanItemSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    
    class Meta:
        model = StudyPlanItem
        fields = ['id', 'topic', 'topic_name', 'scheduled_date', 'is_completed']


class StudyPlanSerializer(serializers.ModelSerializer):
    items = StudyPlanItemSerializer(many=True, read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = StudyPlan
        fields = ['id', 'subject', 'subject_name', 'exam_date', 'hours_per_day', 
                  'created_at', 'items']


class ChatMessageSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'topic', 'topic_name', 'user_message', 'ai_response', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat request"""
    topic_id = serializers.IntegerField()
    message = serializers.CharField()


class StudySessionSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)

    class Meta:
        model = StudySession
        fields = ['id', 'topic', 'topic_name', 'started_at', 'ended_at', 'duration_seconds']
        read_only_fields = ['ended_at', 'duration_seconds']
    
    def create(self, validated_data):
        # Auto-set started_at to now if not provided
        if 'started_at' not in validated_data:
            validated_data['started_at'] = timezone.now()
        return super().create(validated_data)
