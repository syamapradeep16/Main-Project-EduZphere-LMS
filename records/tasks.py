from celery import shared_task
import ollama
from .models import ExamResult

@shared_task
def generate_ai_review(result_id, score, total_marks, exam_title):
    try:
        result = ExamResult.objects.get(id=result_id)
        
        response = ollama.chat(model='llama3.2', messages=[
            {
                'role': 'user',
                'content': f"Provide a brief, professional tutor review for a student who scored {score} out of {total_marks} on their {exam_title} exam. Mention one specific area of Python they should study next."
            },
        ])
        
        result.ai_review = response['message']['content']
        result.save()
    except Exception as e:
        print(f"Celery AI Error: {e}")