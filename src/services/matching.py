from sqlalchemy import select, and_, not_
from sqlalchemy.orm import selectinload
from ..models.models import User, Like, Gender
from ..database.core import async_session
from .cache import RedisCache
from geopy.distance import geodesic
from typing import List, Optional
import logging
import random

logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(self):
        self.cache = RedisCache()

    async def get_next_candidate(self, user_id: int) -> Optional[User]:
        """Получить следующего кандидата для просмотра"""
        try:
            async with async_session() as session:
                # Получаем текущего пользователя
                current_user = await session.get(User, user_id)
                if not current_user:
                    logger.error(f"Пользователь {user_id} не найден")
                    return None

                # Получаем уже просмотренные анкеты
                viewed_query = select(Like.to_user_id).where(Like.from_user_id == user_id)
                viewed_results = await session.execute(viewed_query)
                viewed_ids = [row[0] for row in viewed_results]
                viewed_ids.append(user_id)  # Добавляем свой ID

                # Формируем базовый запрос
                query = (
                    select(User)
                    .options(selectinload(User.photos))
                    .where(
                        and_(
                            User.id.notin_(viewed_ids),
                            User.is_visible == True,
                            User.age.between(
                                current_user.min_age,
                                current_user.max_age
                            )
                        )
                    )
                )

                # Добавляем фильтр по полу, если указаны предпочтения
                if current_user.preferred_gender:
                    query = query.where(User.gender == current_user.preferred_gender)

                # Получаем всех подходящих кандидатов
                results = await session.execute(query)
                candidates = results.scalars().all()

                # Фильтруем по расстоянию
                suitable_candidates = []
                for candidate in candidates:
                    distance = self._calculate_distance(current_user, candidate)
                    if distance <= current_user.max_distance:
                        suitable_candidates.append(candidate)

                if not suitable_candidates:
                    logger.info(f"Подходящие кандидаты для пользователя {user_id} не найдены")
                    return None

                # Выбираем случайного кандидата из подходящих
                return random.choice(suitable_candidates)

        except Exception as e:
            logger.error(f"Ошибка при поиске кандидата: {str(e)}")
            return None

    async def create_like(self, from_user_id: int, to_user_id: int) -> bool:
        """Создать лайк и проверить взаимность"""
        try:
            async with async_session() as session:
                # Проверяем взаимный лайк
                mutual_like = await session.execute(
                    select(Like).where(
                        Like.from_user_id == to_user_id,
                        Like.to_user_id == from_user_id
                    )
                )
                
                # Создаем новый лайк
                like = Like(from_user_id=from_user_id, to_user_id=to_user_id)
                session.add(like)
                await session.commit()
                
                return bool(mutual_like.scalar_one_or_none())
        except Exception as e:
            logger.error(f"Ошибка при создании лайка: {str(e)}")
            return False

    def _calculate_distance(self, user1: User, user2: User) -> float:
        """Рассчитать расстояние между пользователями"""
        try:
            return round(geodesic(
                (user1.location_lat, user1.location_lon),
                (user2.location_lat, user2.location_lon)
            ).kilometers, 1)
        except Exception as e:
            logger.error(f"Ошибка при расчете расстояния: {str(e)}")
            return float('inf')  # Возвращаем "бесконечность" в случае ошибки

    async def _get_viewed_profiles(self, user_id: int) -> List[int]:
        async with async_session() as session:
            result = await session.execute(
                select(Like.to_user_id).where(Like.from_user_id == user_id)
            )
            return [row[0] for row in result]
