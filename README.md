# Social Media Feed Backend

A high-performance, scalable backend for social media platforms built with Django, GraphQL, and PostgreSQL. Features comprehensive role-based access control (RBAC), real-time interactions, and enterprise-grade security with advanced Redis caching architecture.

![Django](https://img.shields.io/badge/Django-4.2.7-green?style=flat&logo=django)
![GraphQL](https://img.shields.io/badge/GraphQL-Graphene-pink?style=flat&logo=graphql)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?style=flat&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7+-red?style=flat&logo=redis)
![Python](https://img.shields.io/badge/Python-3.11+-yellow?style=flat&logo=python)

## 🚀 Features

### Core Features

- **GraphQL API** with Graphene-Django for flexible querying
- **Role-Based Access Control (RBAC)** with 46+ granular permissions
- **Activity Logging** for comprehensive audit trails
- **Email OTP Verification** for secure user registration
- **JWT Authentication** with refresh token support
- **Advanced Redis Caching** with multi-database architecture
- **Rate Limiting** to prevent abuse and ensure stability
- **Pagination** for efficient large dataset handling

### Social Media Features

- **Posts** - Create, read, update, delete with media support
- **Comments** - Nested commenting system with replies
- **Likes & Shares** - Real-time engagement tracking with Redis counters
- **Follow System** - User relationships and social graphs
- **Media Management** - Image/video upload and processing
- **Real-time Interactions** - Live updates for social features
- **Personalized Feeds** - Cached user feeds with intelligent invalidation
- **Trending Posts** - Redis sorted sets for trending content

### Security & Performance

- **Comprehensive Permission System** - 2 roles, 46+ permissions
- **Activity Monitoring** - Track all user actions with metadata
- **Rate Limiting** - Protect against DDoS and abuse
- **Multi-Database Redis Caching** - Specialized caches for different data types
- **Database Optimization** - Strategic indexing for high performance
- **Input Validation** - XSS and injection protection

## 🏗️ Architecture

```
social_media_feed_backend/
├── apps/                          # Django applications
│   ├── core/                      # Shared utilities, permissions & Redis service
│   ├── users/                     # User management & RBAC
│   ├── posts/                     # Post management with feed caching
│   ├── interactions/              # Likes, comments, shares with Redis counters
│   └── analytics/                 # Usage analytics (optional)
├── graphql_api/                   # GraphQL schema configuration
├── config/                        # Django settings and configuration
├── tests/                         # Comprehensive test suite
├── scripts/                       # Utility and deployment scripts
└── docs/                          # API documentation
```

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend Framework** | Django 4.2.7 | Core web framework |
| **API Layer** | GraphQL (Graphene) | Flexible data querying |
| **Database** | PostgreSQL 15+ | Primary data storage |
| **Cache** | Redis 7+ (Multi-DB) | Specialized caching layers |
| **Authentication** | JWT | Secure token-based auth |
| **Email** | Django Email Backend | OTP verification |
| **Media Storage** | Django FileField | Image/video handling |
| **Task Queue** | Celery with Redis | Background processing |

## ⚡ Advanced Redis Caching Architecture

### Multi-Database Redis Configuration

Our Redis setup uses 6 specialized databases for optimal performance:

```python
# Database allocation:
# DB 0: Default cache (general data)
# DB 1: Main application cache (posts, feeds, user data)
# DB 2: Session storage
# DB 3: Real-time counters (likes, comments, shares)
# DB 4: Celery message broker
# DB 5: Celery results backend
```

### Cache Categories

#### 1. **Application Cache (DB 1)**

- **Feed Caching**: User personalized feeds with pagination
- **Post Details**: Individual post data with metadata
- **User Profiles**: Profile information and relationships
- **TTL**: 5-30 minutes for dynamic content

#### 2. **Session Cache (DB 2)**

- **User Sessions**: Django session storage
- **JWT Token Blacklist**: Logout and security
- **TTL**: 24 hours for sessions

#### 3. **Counter Cache (DB 3)**

- **Real-time Counters**: Likes, comments, shares count
- **User Stats**: Followers, following counts
- **Engagement Metrics**: Post interaction statistics
- **TTL**: Persistent (no expiration)

#### 4. **Specialized Operations**

- **Sorted Sets**: Trending posts ranking
- **Redis Sets**: User like tracking, follow relationships
- **Redis Lists**: Activity feeds, recent interactions
- **Pub/Sub**: Real-time notifications (future feature)

### Caching Features

#### Feed Cache Service

```python
# Intelligent feed caching with versioning
- Personalized user feeds with pagination
- Smart cache invalidation on new posts
- Feed versioning to prevent stale data
- Hash-based cache keys for efficiency
```

#### Real-time Counters

```python
# Redis counters for instant updates
post_likes = redis_service.get_counter(f"post:{post_id}:likes")
redis_service.increment_counter(f"post:{post_id}:comments", 1)
```

#### Performance Monitoring

```python
# Built-in performance monitoring
@monitor_performance("user_feed")
@require_permission(Permissions.POST_READ, resource="post", log_activity=True)
def resolve_user_feed(self, info, page=1, items_per_page=10):
    # Cached feed resolution with fallback
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Git

**OR**

- Docker & Docker Compose (for containerized setup)

### Installation

#### Option 1: Local Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/muhabme/social-media-feed-backend.git
   cd social-media-feed-backend
   ```

2. **Set up virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   # Ensure Redis configuration matches your setup:
   # REDIS_HOST=localhost
   # REDIS_PORT=6379
   ```

5. **Set up database**

   ```bash
   python manage.py migrate
   ```

6. **Create superuser**

   ```bash
   python manage.py createsuperuser
   ```

7. **Load sample data (optional)**

   ```bash
   python -m scripts.seed_data
   ```

8. **Start Redis server**

   ```bash
   redis-server
   # Verify Redis is running on all required databases:
   # redis-cli ping
   ```

9. **Start Celery worker (optional, for background tasks)**

   ```bash
   celery -A config worker -l info
   ```

10. **Run development server**

    ```bash
    python manage.py runserver
    ```

11. **Access GraphQL Playground**

    ```
    http://localhost:8000/graphql/
    ```

#### Option 2: Docker Compose Setup (Recommended)

1. **Clone the repository**

   ```bash
   git clone https://github.com/muhabme/social-media-feed-backend.git
   cd social-media-feed-backend
   ```

2. **Choose your environment setup**

   **For Development:**

   ```bash
   cp .env.development .env
   # Edit .env with your development configuration
   ```

   **For Production:**

   ```bash
   cp .env.production .env
   # Edit .env with your production configuration (update domains, secrets, etc.)
   ```

3. **Start services based on environment**

   **Development Mode:**

   ```bash
   # Uses Django development server with Redis cluster
   docker compose up --build -d
   ```

   **Production Mode:**

   ```bash
   # Uses Gunicorn with optimized Redis settings
   docker compose -f docker-compose.prod.yml up --build -d
   ```

   This will start:
   - Django application server (dev server or Gunicorn)
   - PostgreSQL database
   - Redis cache server (configured for multi-database usage)
   - Celery worker and beat scheduler
   - Nginx reverse proxy (production only)
   - All services networked together automatically

4. **Run initial setup**

   **Development:**

   ```bash
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

   **Production:**

   ```bash
   docker compose -f docker-compose.prod.yml exec web python manage.py migrate
   docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
   ```

5. **Load sample data (optional)**

   **Development:**

   ```bash
   docker compose exec web python -m scripts.seed_data
   ```

   **Production:**

   ```bash
   docker compose -f docker-compose.prod.yml exec web python -m scripts.seed_data
   ```

6. **Verify Redis setup**

   ```bash
   # Check Redis multi-database setup
   docker compose exec redis redis-cli ping
   docker compose exec redis redis-cli -n 1 ping  # Application cache
   docker compose exec redis redis-cli -n 2 ping  # Sessions
   docker compose exec redis redis-cli -n 3 ping  # Counters
   ```

7. **Access the application**

   **Development:**
   - GraphQL Playground: `http://localhost:8000/graphql/`

   **Production:**
   - Application: `http://localhost` (port 80)
   - HTTPS: `https://localhost` (port 443, requires SSL setup)

## 🔒 Authentication & Authorization

### User Registration with Email OTP

```graphql
# 1. Register user (sends OTP to email)
mutation {
  registerUser(
    username: "newuser"
    email: "user@example.com"
    password: "securepassword"
    firstName: "John"
    lastName: "Doe"
    bio: "Hello, I'm new here!"
  ) {
    user {
      id
      username
      email
    }
    success
    message
  }
}

# 2. Verify OTP to complete registration
mutation {
  verifyEmailOtp(
    email: "user@example.com"
    otpCode: "123456"
  ) {
    success
    message
    user {
      id
      username
      email
    }
  }
}
```

### JWT Authentication

```graphql
# Login
mutation {
  tokenAuth(username: "user", password: "password") {
    token
    user {
      id
      username
      email
    }
  }
}
```

## 🛡️ Role-Based Access Control (RBAC)

### Roles & Permissions

| Role | Permissions | Description |
|------|-------------|-------------|
| **User** | 22 permissions | Basic social media interactions |
| **Admin** | 46+ permissions | Full system access and management |

### Permission Categories

- **User Management** (7): Profile management, user operations
- **Content Management** (16): Posts, comments, media handling  
- **Social Features** (9): Likes, shares, follows
- **System Features** (6): OTP, notifications
- **Admin Features** (14): System administration, moderation

### Using Permission Decorators

```python
from apps.core.decorators import require_permission
from apps.core.permissions import Permissions

@require_permission(Permissions.POST_CREATE, resource='post', log_activity=True)
def resolve_create_post(self, info, **kwargs):
    # Only users with post:create permission can access
    # Activity is automatically logged
    pass

@require_admin()
def resolve_admin_dashboard(self, info):
    # Admin-only access
    pass
```

## 📊 GraphQL API Examples

### Authentication

#### Register User

```graphql
mutation {
  registerUser(
    username: "newuser"
    email: "user@example.com"
    password: "securepassword"
    firstName: "John"
    lastName: "Doe"
    bio: "Hello, I'm new here!"
  ) {
    user {
      id
      username
      email
      firstName
      lastName
    }
    success
    message
  }
}
```

#### Verify Email OTP

```graphql
mutation {
  verifyEmailOtp(
    email: "user@example.com"
    otpCode: "123456"
  ) {
    success
    message
    user {
      id
      username
      email
    }
  }
}
```

#### Login

```graphql
mutation {
  tokenAuth(username: "newuser", password: "securepassword") {
    token
    user {
      id
      username
      email
    }
  }
}
```

#### Get Current User

```graphql
query {
  me {
    id
    username
    email
    firstName
    lastName
  }
}
```

### Posts with Real-time Data

#### Create Post (Auto-cached)

```graphql
mutation {
  createPost(content: "Hello, World!", imageUrl: "https://example.com/image.jpg") {
    post {
      id
      content
      image
      author {
        username
      }
      createdAt
      likesCount        # Real-time from Redis counter
      commentsCount     # Real-time from Redis counter
      sharesCount       # Real-time from Redis counter
    }
    success
    message
  }
}
```

#### Get User Feed (Cached & Personalized)

```graphql
query {
  userFeed(page: 1, itemsPerPage: 10) {
    items {
      id
      content
      image
      author {
        username
        firstName
        lastName
      }
      likesCount        # Real-time Redis counters
      commentsCount     # Real-time Redis counters
      sharesCount       # Real-time Redis counters
      isLiked          # Cached user interaction state
      createdAt
    }
    totalItems
    totalPages
    currentPage
  }
}
```

#### Get Trending Posts (Redis Sorted Sets)

```graphql
query {
  trendingPosts(page: 1, itemsPerPage: 10) {
    items {
      id
      content
      author {
        username
      }
      likesCount        # Real-time trending score
      commentsCount
      sharesCount
      createdAt
    }
    totalItems
    totalPages
  }
}
```

#### Get Posts by User (Cached)

```graphql
query {
  postsByUser(userId: 1, page: 1, itemsPerPage: 10) {
    items {
      id
      content
      image
      likesCount
      commentsCount
      sharesCount
      createdAt
    }
    totalItems
    totalPages
  }
}
```

### Real-time Interactions

#### Like Post (Updates Redis Counters)

```graphql
mutation {
  likePost(postId: 1) {
    like {
      id
      user {
        username
      }
      post {
        id
        likesCount    # Instantly updated counter
      }
    }
    success
    message
    isLiked
  }
}
```

#### Create Comment (Auto-increments Counters)

```graphql
mutation {
  createComment(postId: 1, content: "Great post!") {
    comment {
      id
      content
      author {
        username
      }
      post {
        commentsCount  # Real-time updated
      }
      createdAt
    }
    success
    message
  }
}
```

#### Share Post (Updates Trending Score)

```graphql
mutation {
  sharePost(postId: 1) {
    share {
      id
      user {
        username
      }
      post {
        id
        content
        sharesCount    # Real-time counter update
      }
      createdAt
    }
    success
    message
  }
}
```

### Performance Queries

#### Get Post with Real-time Stats

```graphql
query {
  post(id: 1) {
    id
    content
    author {
      username
    }
    likesCount        # From Redis counter DB 3
    commentsCount     # From Redis counter DB 3
    sharesCount       # From Redis counter DB 3
    isLiked          # From Redis set lookup
    createdAt
  }
}
```

## 🚦 Rate Limiting

Built-in rate limiting protects against abuse:

- **GraphQL API**: 10 requests per minute per user/IP
- **All POST requests**: Limited to authenticated users or by IP address
- **Redis-backed**: Uses Redis counters for distributed rate limiting
- **Graceful handling**: Returns HTTP 429 with JSON error message when limits exceeded
- **Smart identification**: Uses user ID for authenticated requests, falls back to IP address
- **X-Forwarded-For support**: Properly handles requests behind proxies/load balancers

## ⚡ Caching Strategy Deep Dive

### Redis Multi-Database Architecture

```python
CACHES = {
    "default": {
        # DB 1: Main application cache
        "LOCATION": REDIS_URL + "/1",
        "TIMEOUT": 300,  # 5 minutes default
        "OPTIONS": {
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        }
    },
    "sessions": {
        # DB 2: User sessions
        "LOCATION": REDIS_URL + "/2",
        "TIMEOUT": 86400,  # 24 hours
    },
    "counters": {
        # DB 3: Real-time counters (never expire)
        "LOCATION": REDIS_URL + "/3",
        "TIMEOUT": None,
    }
}
```

### Cache Usage Patterns

#### 1. **Feed Caching**

- **User Personalized Feeds**: Cached with pagination metadata
- **Smart Invalidation**: Version-based cache invalidation
- **Hash-based Keys**: Efficient cache key generation
- **Fallback Strategy**: Database fallback for cache misses

#### 2. **Real-time Counters**

- **Like Counts**: `post:{id}:likes` counter
- **Comment Counts**: `post:{id}:comments` counter  
- **Share Counts**: `post:{id}:shares` counter
- **User Stats**: Follower/following counts

#### 3. **Trending Algorithm**

- **Redis Sorted Sets**: Score-based trending posts
- **Engagement Scoring**: Weighted likes, comments, shares
- **Time Decay**: Automatic score adjustment over time

#### 4. **User Interaction State**

- **Like State**: Redis sets for instant `isLiked` checks
- **Follow State**: Cached relationship status
- **Activity Tracking**: Recent user actions

### Cache Performance Optimizations

- **Connection Pooling**: 20 max connections with retry logic
- **Compression**: ZLib compression for large data
- **JSON Serialization**: Fast serialization/deserialization
- **Strategic TTL**: Different timeouts for different data types
- **Batch Operations**: Bulk cache operations where possible

## 📈 Performance Optimizations

### Database

- **Strategic Indexing**: All foreign keys, timestamps, and query fields
- **Query Optimization**: `select_related()` and `prefetch_related()`
- **Soft Deletes**: Maintain referential integrity
- **Connection Pooling**: Efficient database connections

### Redis Performance

- **Multi-Database Separation**: Isolated workloads for optimal performance
- **Pipeline Operations**: Batch Redis commands
- **Connection Health Checks**: Automatic connection monitoring
- **Memory Optimization**: Compressed data storage

### Application

- **Pagination**: Limit result sets to prevent memory issues
- **Lazy Loading**: Load related data only when needed
- **Background Tasks**: Async processing with Celery
- **Response Compression**: Reduce bandwidth usage
- **Performance Monitoring**: Built-in execution time tracking

### GraphQL Optimizations

- **Query Complexity Analysis**: Prevent expensive queries
- **DataLoader Pattern**: N+1 query prevention
- **Field-level Caching**: Cache expensive field resolutions
- **Batch Loading**: Efficient related data loading

## 🧪 Testing

### Run Tests

```bash
# Local development
python manage.py test

# Docker development
docker compose exec web python manage.py test

# Docker production  
docker compose -f docker-compose.prod.yml exec web python manage.py test

# Specific app
python manage.py test apps.posts
# Test Redis functionality
python manage.py test apps.core.tests.test_redis_service

# With coverage (local)
coverage run --source='.' manage.py test
coverage report
coverage html

# With coverage (Docker)
docker compose exec web coverage run --source='.' manage.py test
docker compose exec web coverage report
```

### Test Categories

- **Unit Tests**: Model methods, utilities, permissions
- **Integration Tests**: GraphQL API endpoints
- **Cache Tests**: Redis operations and cache invalidation
- **Performance Tests**: Database query optimization and cache hit rates
- **Security Tests**: Authentication, authorization, input validation

### Redis Testing

```bash
# Test Redis connectivity
python manage.py shell
>>> from apps.core.redis_service import redis_service
>>> redis_service.redis_client.ping()  # Should return True

# Test counter operations
>>> redis_service.increment_counter("test:counter", 5)
>>> redis_service.get_counter("test:counter")  # Should return 5
```

## 📦 Deployment

### Environment Configuration

The application supports multiple environment configurations with optimized Redis settings:

#### Development Environment

```bash
# .env.development
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=dev-secret-key-not-for-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
REDIS_HOST=redis
REDIS_PORT=6379
DB_PASSWORD=postgres
# ... other dev settings
```

#### Production Environment

```bash
# .env.production
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-very-long-secure-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
REDIS_HOST=your-redis-cluster.com
REDIS_PORT=6379
DB_PASSWORD=very_secure_production_password
# Redis optimization settings
REDIS_CONNECTION_POOL_SIZE=50
REDIS_TIMEOUT=5
# ... other production settings
```

### Docker Deployment Options

#### Production Features

- **Multi-stage build**: Smaller, optimized images
- **Gunicorn with Gevent**: Async workers for better performance
- **Redis Cluster Support**: Horizontal scaling for Redis
- **Connection Pooling**: Optimized Redis connections
- **Health Checks**: Container and Redis monitoring
- **Production logging**: Structured logs for monitoring

### Cache Monitoring & Maintenance

#### Redis Monitoring Commands

```bash
# Monitor Redis performance
redis-cli info stats
redis-cli info memory

# Check specific database usage
redis-cli -n 1 dbsize  # Application cache
redis-cli -n 2 dbsize  # Sessions  
redis-cli -n 3 dbsize  # Counters

# Monitor real-time operations
redis-cli monitor
```

#### Cache Maintenance Scripts

```bash
# Clear specific caches
python manage.py shell
>>> from apps.posts.cache_service import feed_cache_service
>>> feed_cache_service.invalidate_user_feed(user_id=1)

# Bulk cache operations
>>> from apps.core.redis_service import redis_service
>>> redis_service.redis_client.flushdb()  # Clear current database
```

## 📚 API Documentation

### GraphQL Playground

Access interactive API documentation at `/graphql/` when `DEBUG=True`.

### Performance Monitoring

All GraphQL resolvers include performance monitoring:

```python
@monitor_performance("user_feed")  # Tracks execution time
@login_required
@require_permission(Permissions.POST_READ, resource="post", log_activity=True)
def resolve_user_feed(self, info, page=1, items_per_page=10):
    # Monitored resolver with caching
```

### Cache Headers

API responses include cache-related headers:

- `X-Cache-Status`: HIT/MISS/BYPASS
- `X-Cache-TTL`: Time to live for cached data
- `X-Redis-DB`: Which Redis database served the request

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests including Redis functionality (`python manage.py test`)
4. Commit changes (`git commit -m 'feat: add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Commit Convention

- `feat:` New features
- `fix:` Bug fixes
- `cache:` Caching improvements
- `perf:` Performance improvements
- `docs:` Documentation updates
- `test:` Test additions/updates

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] **Real-time Notifications** with Redis Pub/Sub
- [ ] **Advanced Analytics** dashboard with cached metrics
- [ ] **Content Moderation** with AI and cached rules
- [ ] **Multi-language Support** i18n with cached translations
- [ ] **Redis Cluster** for horizontal scaling
- [ ] **Advanced Caching** strategies (Write-through, Write-behind)
- [ ] **GraphQL Subscriptions** with Redis backing
- [ ] **Cache Warming** strategies for optimal performance

## 🆘 Support

- **Documentation**: Check the `/docs` folder
- **Issues**: [GitHub Issues](https://github.com/muhabme/social-media-feed-backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/muhabme/social-media-feed-backend/discussions)
- **Performance Issues**: Include Redis stats and cache hit rates

## ⭐ Star History

If this project helps you, please give it a star! ⭐

---
