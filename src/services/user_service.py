from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from ..models.models import User, Photo
from ..database.core import async_session
from geopy.distance import geodesic
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class UserService:
    async def create_user(self, data: dict) -> Optional[User]:
        try:
            async with async_session() as session:
                user = User(
                    tg_id=data['tg_id'],
                    username=data.get('username'),
                    name=data['name'],
                    age=data['age'],
                    gender=data['gender'],
                    preferred_gender=data['preferred_gender'],
                    bio=data.get('bio', ''),
                    location_lat=data['location_lat'],
                    location_lon=data['location_lon'],
                    city=data.get('city'),
                    is_visible=data.get('is_visible', True),
                    min_age=data.get('min_age', 18),
                    max_age=data.get('max_age', 100),
                    max_distance=data.get('max_distance', 50)
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                if 'photo' in data:
                    photo = Photo(user_id=user.id, file_id=data['photo'])
                    session.add(photo)
                    await session.commit()
                
                return user
                
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {str(e)}")
            return None

    async def get_user_by_tg_id(self, tg_id: int) -> Optional[User]:
        async with async_session() as session:
            query = (
                select(User)
                .options(selectinload(User.photos))
                .where(User.tg_id == tg_id)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        async with async_session() as session:
            query = (
                select(User)
                .options(selectinload(User.photos))
                .where(User.id == user_id)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def update_user(self, user_id: int, data: dict) -> Optional[User]:
        try:
            async with async_session() as session:
                query = select(User).where(User.id == user_id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                
                if user:
                    for key, value in data.items():
                        setattr(user, key, value)
                    await session.commit()
                    await session.refresh(user)
                    return user
                return None
                
        except Exception as e:
            logger.error(f"Ошибка обновления пользователя: {str(e)}")
            return None

    async def toggle_visibility(self, tg_id: int) -> Optional[User]:
        try:
            async with async_session() as session:
                query = (
                    select(User)
                    .where(User.tg_id == tg_id)
                )
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                
                if user:
                    return user
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя: {str(e)}")
            return None

    async def calculate_distance(self, user1: User, user2: User) -> float:
        return round(geodesic(
            (user1.location_lat, user1.location_lon),
            (user2.location_lat, user2.location_lon)
        ).kilometers, 1)

    async def add_photo(self, user_id: int, file_id: str) -> Optional[Photo]:
        try:
            async with async_session() as session:
                photo = Photo(user_id=user_id, file_id=file_id)
                session.add(photo)
                await session.commit()
                return photo
        except Exception as e:
            logger.error(f"Ошибка добавления фото: {str(e)}")
            return None

    async def delete_user_by_tg_id(self, tg_id: int) -> bool:
        try:
            async with async_session() as session:
                async with session.begin():
                    user = await self.get_user_by_tg_id(tg_id)
                    if user:
                        await session.delete(user)
                        return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя: {str(e)}")
            return False

    async def update_photo(self, user_id: int, file_id: str) -> bool:
        try:
            async with async_session() as session:
                # Сначала удаляем старые фото
                delete_query = delete(Photo).where(Photo.user_id == user_id)
                await session.execute(delete_query)
                
                # Добавляем новое фото
                new_photo = Photo(user_id=user_id, file_id=file_id)
                session.add(new_photo)
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления фото: {str(e)}")
            return False