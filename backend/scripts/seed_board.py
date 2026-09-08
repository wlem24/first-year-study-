"""Seed initial sample 1st-grade activities onto the school board."""
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath("backend"))

from app.database import init_db, AsyncSessionLocal
from app.models import Post

async def seed_samples():
    await init_db()

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        count = (await session.execute(select(func.count(Post.id)))).scalar_one()
        if count == 0:
            posts_data = [
                {
                    "title": "Rainbow Butterfly Watercolor",
                    "description": "Mayan painted a colourful butterfly in art class today using watercolours and glitter outlines!",
                    "category": "art",
                    "subject": "Watercolor Painting",
                    "star_rating": 5,
                    "teacher_note": "Amazing color blending and gentle brushwork! 🌟",
                },
                {
                    "title": "The Little Red Hen Story Reading",
                    "description": "Practiced phonics sounds and read the whole story aloud with Mom!",
                    "category": "reading",
                    "subject": "Phonics & Storytime",
                    "star_rating": 5,
                    "teacher_note": "Clear reading voice and great confidence! 📚",
                },
                {
                    "title": "Counting by 10s to 100 Rocket",
                    "description": "Completed the math rocket challenge and solved all 10s number bonds perfectly!",
                    "category": "math",
                    "subject": "Number Bonds",
                    "star_rating": 5,
                    "teacher_note": "Super fast math calculations! 100% score! 🚀",
                },
                {
                    "title": "Bean Seed Sprout Experiment",
                    "description": "Planted a tiny kidney bean in cotton wool and drew its first two green leaves in science notebook.",
                    "category": "science",
                    "subject": "Plant Biology",
                    "star_rating": 5,
                    "teacher_note": "Great observation skills and neat science drawing! 🌱",
                },
                {
                    "title": "1st Grade Star Student of the Week",
                    "description": "Awarded for helping classmates clean up art supplies and sharing crayons with a smile!",
                    "category": "badges",
                    "subject": "Classroom Badge",
                    "star_rating": 5,
                    "teacher_note": "A wonderful, kind helper in our 1st grade class! 💖",
                },
            ]

            for p_data in posts_data:
                post = Post(**p_data)
                session.add(post)

            await session.commit()
            print("Successfully seeded 5 initial 1st-grade school activities!")
        else:
            print(f"Board already contains {count} activities.")

if __name__ == "__main__":
    asyncio.run(seed_samples())
