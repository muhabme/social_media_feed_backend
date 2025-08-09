import os
import random
from faker import Faker

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from django.contrib.auth.models import User
from apps.users.models import UserProfile, Follow, Role
from apps.posts.models import Post
from apps.interactions.models import Like, Comment, Share

fake = Faker()


def seed_users(n=10):
    users = []
    for i in range(n):
        username = f"user{i+1}"
        user = User.objects.create_user(
            username=username, email=f"{username}@example.com", password="password123"
        )
        UserProfile.objects.create(
            user=user,
            bio=fake.text(max_nb_chars=120),
            profile_picture="",
            role=Role.objects.filter(name="user").first(),
        )
        users.append(user)
    return users


def seed_posts(users, n=50):
    posts = []
    for i in range(n):
        author = random.choice(users)
        post = Post.objects.create(
            author=author, content=fake.paragraph(nb_sentences=3), image=None
        )
        posts.append(post)
    return posts


def seed_likes(users, posts):
    for post in posts:
        likers = random.sample(users, random.randint(0, len(users)))
        for user in likers:
            Like.objects.get_or_create(user=user, post=post)


def seed_comments(users, posts):
    for post in posts:
        commenters = random.sample(users, random.randint(0, len(users)))
        for user in commenters:
            Comment.objects.create(author=user, post=post, content=fake.sentence())


def seed_shares(users, posts):
    for post in posts:
        sharers = random.sample(users, random.randint(0, len(users) // 2))
        for user in sharers:
            Share.objects.get_or_create(user=user, post=post)


def seed_follows(users):
    for user in users:
        others = [u for u in users if u != user]
        following = random.sample(others, random.randint(0, len(others) // 2))
        for followed_user in following:
            Follow.objects.get_or_create(follower=user, following=followed_user)


def run():
    print("Seeding database...")
    Follow.objects.all().delete()
    User.objects.all().delete()
    Post.objects.all().delete()
    Like.objects.all().delete()
    Comment.objects.all().delete()
    Share.objects.all().delete()
    UserProfile.objects.all().delete()

    users = seed_users(10)
    posts = seed_posts(users, 50)
    seed_likes(users, posts)
    seed_comments(users, posts)
    seed_shares(users, posts)
    seed_follows(users)

    print("Seeding completed!")


if __name__ == "__main__":
    run()
