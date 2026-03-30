# records/forms.py
from django import forms
from .models import Exam, MCQQuestion

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'total_marks', 'exam_date']
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Exam Title'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }

        # records/forms.py
from .models import MCQQuestion

class MCQQuestionForm(forms.ModelForm):
    class Meta:
        model = MCQQuestion
        fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'option_a': forms.TextInput(attrs={'class': 'form-control'}),
            'option_b': forms.TextInput(attrs={'class': 'form-control'}),
            'option_c': forms.TextInput(attrs={'class': 'form-control'}),
            'option_d': forms.TextInput(attrs={'class': 'form-control'}),
            'correct_option': forms.Select(attrs={'class': 'form-control'}),
        }