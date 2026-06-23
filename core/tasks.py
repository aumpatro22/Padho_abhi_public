"""
Background task functions for async AI content generation.
Uses Django-Q2 for task scheduling and execution.
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def generate_content_task(topic_id: int, user_id: int, api_key: str = None):
    """
    Background task to generate all AI content for a topic.
    This runs asynchronously to prevent blocking the request.
    """
    from .models import Topic, Note, Mindmap, Flashcard, MCQQuestion, UserProfile, AITask
    from .ai_service import gemini_service
    from django.contrib.auth.models import User
    
    try:
        topic = Topic.objects.get(pk=topic_id)
        user = User.objects.get(pk=user_id)
        
        # Update task status
        task, _ = AITask.objects.get_or_create(
            topic=topic,
            user=user,
            task_type='generate_all',
            defaults={'status': 'processing'}
        )
        task.status = 'processing'
        task.started_at = timezone.now()
        task.save()
        
        subject_name = topic.unit.subject.name
        
        # Generate all content
        content = gemini_service.generate_all_content(topic.name, subject_name, api_key=api_key)
        
        # Check for errors
        errors = []
        if isinstance(content.get('notes'), dict) and 'error' in content['notes']:
            errors.append(f"Notes: {content['notes']['error']}")
        if isinstance(content.get('mindmap'), dict) and 'error' in content['mindmap']:
            errors.append(f"Mindmap: {content['mindmap']['error']}")
        if isinstance(content.get('flashcards'), dict) and 'error' in content['flashcards']:
            errors.append(f"Flashcards: {content['flashcards']['error']}")
        if isinstance(content.get('mcqs'), dict) and 'error' in content['mcqs']:
            errors.append(f"MCQs: {content['mcqs']['error']}")
        
        if errors:
            task.status = 'failed'
            task.error_message = '; '.join(errors)
            task.completed_at = timezone.now()
            task.save()
            return {'status': 'failed', 'errors': errors}
        
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
            mindmap_data = content['mindmap']
            if 'usage' in mindmap_data:
                del mindmap_data['usage']
            Mindmap.objects.update_or_create(
                topic=topic,
                defaults={'json_data': mindmap_data}
            )
        
        # Save flashcards
        if 'flashcards' in content and content['flashcards']:
            # Clear existing flashcards
            topic.flashcards.all().delete()
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
            # Clear existing MCQs
            topic.mcqs.all().delete()
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
        
        # Update token usage
        if content.get('usage'):
            try:
                profile = user.profile
                profile.total_input_tokens += content['usage'].get('input', 0)
                profile.total_output_tokens += content['usage'].get('output', 0)
                profile.save(update_fields=['total_input_tokens', 'total_output_tokens'])
            except Exception as e:
                logger.error(f"Failed to update token usage: {e}")
        
        # Mark task as completed
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.result = {
            'notes': 'notes' in content,
            'mindmap': 'mindmap' in content,
            'flashcards': len(content.get('flashcards', [])),
            'mcqs': len(content.get('mcqs', []))
        }
        task.save()
        
        logger.info(f"Content generation completed for topic {topic_id}")
        return {'status': 'completed', 'result': task.result}
        
    except Exception as e:
        logger.error(f"Content generation failed for topic {topic_id}: {e}")
        try:
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = timezone.now()
            task.save()
        except:
            pass
        return {'status': 'failed', 'error': str(e)}


def generate_notes_task(topic_id: int, user_id: int, api_key: str = None):
    """Background task to generate notes for a topic."""
    from .models import Topic, Note, AITask
    from .ai_service import gemini_service
    from django.contrib.auth.models import User
    
    try:
        topic = Topic.objects.get(pk=topic_id)
        user = User.objects.get(pk=user_id)
        
        task, _ = AITask.objects.update_or_create(
            topic=topic,
            user=user,
            task_type='generate_notes',
            defaults={'status': 'processing', 'started_at': timezone.now()}
        )
        
        subject_name = topic.unit.subject.name
        notes_data = gemini_service.generate_notes(topic.name, subject_name, api_key=api_key)
        
        if 'error' in notes_data:
            task.status = 'failed'
            task.error_message = notes_data['error']
            task.completed_at = timezone.now()
            task.save()
            return {'status': 'failed', 'error': notes_data['error']}
        
        Note.objects.update_or_create(
            topic=topic,
            defaults={
                'summary': notes_data.get('summary', ''),
                'detailed_content': notes_data.get('detailed_content', ''),
                'analogies': notes_data.get('analogies', []),
                'diagram_description': notes_data.get('diagram_description', '')
            }
        )
        
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        return {'status': 'completed'}
        
    except Exception as e:
        logger.error(f"Notes generation failed for topic {topic_id}: {e}")
        return {'status': 'failed', 'error': str(e)}


def generate_flashcards_task(topic_id: int, user_id: int, api_key: str = None):
    """Background task to generate flashcards for a topic."""
    from .models import Topic, Note, Flashcard, AITask
    from .ai_service import gemini_service
    from django.contrib.auth.models import User
    
    try:
        topic = Topic.objects.get(pk=topic_id)
        user = User.objects.get(pk=user_id)
        
        task, _ = AITask.objects.update_or_create(
            topic=topic,
            user=user,
            task_type='generate_flashcards',
            defaults={'status': 'processing', 'started_at': timezone.now()}
        )
        
        # Get notes content if available
        notes_content = ""
        try:
            notes_content = topic.note.detailed_content or topic.note.summary
        except Note.DoesNotExist:
            pass
        
        flashcards_data = gemini_service.generate_flashcards(topic.name, notes_content, api_key=api_key)
        
        if 'error' in flashcards_data:
            task.status = 'failed'
            task.error_message = flashcards_data['error']
            task.completed_at = timezone.now()
            task.save()
            return {'status': 'failed', 'error': flashcards_data['error']}
        
        # Clear and recreate flashcards
        topic.flashcards.all().delete()
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
        
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        return {'status': 'completed', 'count': topic.flashcards.count()}
        
    except Exception as e:
        logger.error(f"Flashcards generation failed for topic {topic_id}: {e}")
        return {'status': 'failed', 'error': str(e)}
