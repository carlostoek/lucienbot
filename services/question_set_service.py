"""
Servicio de QuestionSet - Lucien Bot

Gestiona conjuntos de preguntas de trivia y su carga desde JSON.
"""
import json
import logging
import random
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from models.models import QuestionSet, Question, Difficulty
from models.database import SessionLocal

logger = logging.getLogger(__name__)


class QuestionSetService:
    """Servicio para gestionar conjuntos de preguntas de trivia"""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def close(self):
        """Cierra la sesion de base de datos"""
        if hasattr(self, 'db') and self.db:
            self.db.close()

    # ==================== QUESTION SET CRUD ====================

    def get_question_sets(self) -> List[QuestionSet]:
        """Obtiene todos los conjuntos de preguntas activos"""
        return self.db.query(QuestionSet).filter(
            QuestionSet.is_active == True
        ).order_by(QuestionSet.created_at.desc()).all()

    def get_question_set(self, set_id: int) -> Optional[QuestionSet]:
        """Obtiene un conjunto de preguntas por ID"""
        return self.db.query(QuestionSet).filter(
            QuestionSet.id == set_id
        ).first()

    def create_question_set(self, data: dict) -> QuestionSet:
        """
        Crea un nuevo conjunto de preguntas.

        Args:
            data: dict con name, description, file_path, is_override

        Returns:
            QuestionSet creado
        """
        question_set = QuestionSet(
            name=data.get('name'),
            description=data.get('description'),
            file_path=data.get('file_path'),
            is_override=data.get('is_override', False),
            is_active=data.get('is_active', True)
        )
        self.db.add(question_set)
        self.db.commit()
        self.db.refresh(question_set)

        logger.info(
            f"question_set_service - create_question_set - "
            f"id:{question_set.id}, name:{question_set.name}"
        )
        return question_set

    # ==================== QUESTIONS ====================

    def get_questions_for_set(self, set_id: int) -> List[Question]:
        """Obtiene todas las preguntas de un conjunto"""
        return self.db.query(Question).filter(
            Question.question_set_id == set_id
        ).all()

    def load_questions_from_json(self, set_id: int) -> List[Question]:
        """
        Carga preguntas desde archivo JSON asociado al QuestionSet.

        El archivo JSON debe tener estructura:
        [
            {
                "question_text": "...",
                "option_a": "...",
                "option_b": "...",
                "option_c": "...",
                "option_d": "...",
                "correct_option": "A",  // A, B, C o D
                "difficulty": "medium",   // easy, medium, hard
                "category": "cultura"
            },
            ...
        ]

        Args:
            set_id: ID del QuestionSet

        Returns:
            Lista de objetos Question creados/actualizados
        """
        question_set = self.get_question_set(set_id)
        if not question_set:
            logger.warning(f"question_set_service - load_questions_from_json - QuestionSet:{set_id} not found")
            return []

        if not question_set.file_path:
            logger.warning(f"question_set_service - load_questions_from_json - QuestionSet:{set_id} has no file_path")
            return []

        file_path = Path(question_set.file_path)
        if not file_path.exists():
            logger.warning(f"question_set_service - load_questions_from_json - File not found: {file_path}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            questions_data = data if isinstance(data, list) else data.get('questions', [])
            questions = []

            for q_data in questions_data:
                # Map difficulty string to enum
                difficulty_str = q_data.get('difficulty', 'medium').lower()
                try:
                    difficulty = Difficulty[difficulty_str.upper()]
                except KeyError:
                    difficulty = Difficulty.MEDIUM

                # Create or update question
                question = Question(
                    question_set_id=set_id,
                    question_text=q_data.get('question_text', ''),
                    option_a=q_data.get('option_a', ''),
                    option_b=q_data.get('option_b', ''),
                    option_c=q_data.get('option_c', ''),
                    option_d=q_data.get('option_d', ''),
                    correct_option=q_data.get('correct_option', 'A').upper(),
                    difficulty=difficulty,
                    category=q_data.get('category')
                )
                questions.append(question)

            # Add all questions
            self.db.add_all(questions)
            self.db.commit()

            logger.info(
                f"question_set_service - load_questions_from_json - "
                f"QuestionSet:{set_id} - loaded:{len(questions)} questions"
            )
            return questions

        except Exception as e:
            logger.error(f"question_set_service - load_questions_from_json - Error: {e}")
            self.db.rollback()
            return []

    def get_random_question(self, set_id: int) -> Tuple[Optional[Question], int]:
        """
        Obtiene una pregunta aleatoria de un conjunto.

        Args:
            set_id: ID del QuestionSet

        Returns:
            Tuple de (Question o None, index en la lista)
        """
        questions = self.get_questions_for_set(set_id)
        if not questions:
            return None, -1

        idx = random.randint(0, len(questions) - 1)
        return questions[idx], idx

    def check_answer(self, question: Question, answer: str) -> bool:
        """
        Verifica si una respuesta es correcta.

        Args:
            question: Question a verificar
            answer: Respuesta del usuario (A, B, C o D)

        Returns:
            True si la respuesta es correcta
        """
        if not question:
            return False
        return question.correct_option.upper() == answer.upper()

    def __del__(self):
        """Cierra la sesion"""
        self.close()