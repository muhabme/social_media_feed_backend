# Social Media Feed Backend Documentation

Welcome to the comprehensive documentation for the Social Media Feed Backend. This documentation covers everything from basic setup to advanced deployment and maintenance.

## 📚 Documentation Structure

### Getting Started

- [Quick Start Guide](./getting-started/quick-start.md) - Get up and running in minutes
- [Installation Guide](./getting-started/installation.md) - Detailed installation instructions
- [Configuration Guide](./getting-started/configuration.md) - Environment and settings configuration
- [Docker Setup](./getting-started/docker-setup.md) - Docker and Docker Compose setup

### API Documentation

- [GraphQL API Overview](./api/graphql-overview.md) - Introduction to the GraphQL API
- [Authentication & Authorization](./api/authentication.md) - User auth, JWT, and permissions
- [Posts API](./api/posts.md) - Post management operations
- [Interactions API](./api/interactions.md) - Likes, comments, shares
- [Users API](./api/users.md) - User management and profiles
- [Admin API](./api/admin.md) - Administrative operations

### Architecture & Design

- [System Architecture](./architecture/system-overview.md) - High-level system design
- [Database Schema](./architecture/database-schema.md) - PostgreSQL database design
- [Redis Architecture](./architecture/redis-architecture.md) - Multi-database caching strategy
- [Permission System](./architecture/permissions.md) - RBAC implementation details

### Performance & Caching

- [Caching Strategy](./performance/caching-strategy.md) - Comprehensive caching guide
- [Redis Operations](./performance/redis-operations.md) - Redis usage patterns
- [Performance Monitoring](./performance/monitoring.md) - Performance tracking and optimization
- [Database Optimization](./performance/database-optimization.md) - PostgreSQL optimization

### Deployment

- [Production Deployment](./deployment/production.md) - Production deployment guide
- [Docker Production](./deployment/docker-production.md) - Production Docker setup
- [Environment Configuration](./deployment/environment-config.md) - Environment variables
- [Monitoring & Logging](./deployment/monitoring.md) - Production monitoring setup

### Development

- [Development Setup](./development/setup.md) - Local development environment
- [Testing Guide](./development/testing.md) - Testing strategies and examples
- [Code Style Guide](./development/code-style.md) - Coding standards and practices
- [Contributing Guide](./development/contributing.md) - How to contribute to the project

### Troubleshooting

- [Common Issues](./troubleshooting/common-issues.md) - Frequently encountered problems
- [Redis Troubleshooting](./troubleshooting/redis-issues.md) - Redis-specific issues
- [Performance Issues](./troubleshooting/performance.md) - Performance debugging
- [FAQ](./troubleshooting/faq.md) - Frequently asked questions

### Examples & Tutorials

- [API Usage Examples](./examples/api-examples.md) - Practical API usage examples
- [Integration Examples](./examples/integration-examples.md) - Frontend integration examples
- [Advanced Queries](./examples/advanced-queries.md) - Complex GraphQL queries
- [Bulk Operations](./examples/bulk-operations.md) - Efficient bulk data operations

## 🚀 Quick Navigation

### For Developers

- New to the project? Start with [Quick Start Guide](./getting-started/quick-start.md)
- Setting up locally? Check [Development Setup](./development/setup.md)
- Need API examples? See [API Usage Examples](./examples/api-examples.md)

### For DevOps/SysAdmins

- Deploying to production? See [Production Deployment](./deployment/production.md)
- Performance issues? Check [Performance Monitoring](./performance/monitoring.md)
- Redis problems? See [Redis Troubleshooting](./troubleshooting/redis-issues.md)

### For Frontend Developers

- Integrating with frontend? See [Integration Examples](./examples/integration-examples.md)
- Understanding auth? Check [Authentication & Authorization](./api/authentication.md)
- Need GraphQL examples? See [GraphQL API Overview](./api/graphql-overview.md)

## 📖 Document Conventions

### Code Examples

All code examples in this documentation are tested and working. They follow this format:

```graphql
# GraphQL Query Example
query {
  userFeed(page: 1, itemsPerPage: 10) {
    items {
      id
      content
      likesCount
    }
  }
}
```

```python
# Python Code Example
from apps.core.redis_service import redis_service

# Get cached data
cached_data = redis_service.get_cached("user_feed:123")
```

### Environment Variables

Environment variables are documented with their purpose and example values:

```env
# Database Configuration
DB_NAME=social_media_prod          # Database name
DB_USER=social_media_user          # Database user
DB_PASSWORD=secure_password        # Database password (required)
```

### API Endpoints

API documentation includes request/response examples:

**Request:**

```json
{
  "query": "query { me { id username email } }"
}
```

**Response:**

```json
{
  "data": {
    "me": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com"
    }
  }
}
```

## 🔄 Documentation Updates

This documentation is actively maintained alongside the codebase. When contributing to the project:

1. Update relevant documentation for any new features
2. Add examples for new API endpoints
3. Update configuration guides for new environment variables
4. Add troubleshooting entries for known issues

## 📞 Support

- **Documentation Issues**: Create an issue with the `documentation` label
- **API Questions**: Check [API Documentation](./api/) or create a discussion
- **Performance Questions**: See [Performance Guide](./performance/) or contact the team
- **Deployment Help**: Check [Deployment Guide](./deployment/) or seek support

---

**Last Updated**: August 2025
