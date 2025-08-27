# Urban Watch Backend API

A FastAPI-based backend service for the Urban Watch mobile application, designed to manage urban issue reporting, AI-powered analysis, and administrative oversight.

## 🌟 Features

- **User Authentication**: Mobile-based signup and login
- **Issue Reporting**: Image upload with GPS location
- **AI Analysis**: Automatic classification of potholes and trash overflow
- **Report Clustering**: Intelligent merging of nearby similar reports
- **Admin Dashboard**: Comprehensive management interface
- **Real-time Processing**: Background queue processing
- **Caching**: Redis-based caching for performance
- **Geospatial Queries**: Location-based report clustering

## 🏗️ Architecture

### Tech Stack
- **Backend Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **Cache/Queue**: Redis
- **AI Models**: YOLOv8 (Ultralytics)
- **Image Processing**: OpenCV, Pillow
- **Authentication**: JWT tokens

### Core Components
- **API Layer**: RESTful endpoints for mobile and admin clients
- **AI Service**: Image analysis for automatic categorization
- **Queue Service**: Background processing for report clustering
- **Cache Service**: Redis-based caching for performance
- **Database Service**: Supabase integration with RLS policies

## 📋 Prerequisites

- Python 3.8+
- Redis server
- Supabase account and project
- Git

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd urban-watch-server
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```

3. **Configure environment variables**
   - Update `.env` file with your Supabase and Redis credentials
   - See `.env.example` for required variables

4. **Set up the database**
   - Run the SQL commands in `database_schema.sql` in your Supabase SQL editor

5. **Start the server**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
All endpoints (except signup/login) require a Bearer token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### Endpoints

#### User Authentication
- `POST /user/signup` - User registration
- `POST /user/login` - User login
- `GET /user/profile` - Get user profile

#### Reports
- `POST /report-issue` - Submit new issue report
- `GET /get-reports` - Get user's reports with filtering

#### Admin (Public endpoints for administration)
- `GET /admin/priority-reports` - Get high-priority reports
- `GET /admin/reports` - Get all reports with pagination
- `GET /admin/reports/{id}` - Get report details
- `PUT /admin/reports/{id}/status` - Update report status
- `GET /admin/reports/summary` - Get dashboard statistics

### API Response Format
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { ... }
}
```

## 🤖 AI Models

The system uses YOLOv8 models for image analysis:

- **Pothole Detection**: `app/ai/models/pothole.pt`
- **Trash Detection**: `app/ai/models/trash_new.pt`

Models automatically:
- Analyze uploaded images
- Calculate confidence scores
- Determine criticality levels
- Generate descriptive reports

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-super-secret-jwt-key
```

## 📊 Database Schema

### Users Table
```sql
- user_id (VARCHAR, PRIMARY KEY)
- mobile_no (VARCHAR, UNIQUE)
- name (VARCHAR)
- address (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

### Reports Table
```sql
- report_id (VARCHAR, PRIMARY KEY)
- user_ids (TEXT[])
- people_reported (INTEGER)
- category (ENUM: potholes, trash_overflow)
- title (VARCHAR)
- ai_analysis (TEXT)
- images (TEXT[])
- location (JSONB)
- criticality_score (INTEGER 1-100)
- status (ENUM: waiting_for_attention, got_the_attention, resolved)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

## 🔄 Background Processing

The system includes a background queue processor that:

1. **Receives new reports** via Redis queue
2. **Runs AI analysis** on uploaded images
3. **Finds nearby reports** within 50m radius
4. **Merges similar reports** or creates new ones
5. **Updates criticality scores** based on crowd reporting

## 📱 Mobile App Integration

### Report Submission Flow
1. User takes photo and provides location
2. Image uploaded to `/report-issue` endpoint
3. Report queued for background processing
4. AI analysis determines category and severity
5. System checks for nearby similar reports
6. Either merges with existing or creates new report

### Response Caching
- User reports cached for 5 minutes
- Priority reports cached for 3 minutes
- Admin summaries cached for 10 minutes

## 🛠️ Development

### Project Structure
```
urban-watch-server/
├── app/
│   ├── api/
│   │   ├── auth/
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── services/
│   ├── ai/                          # AI models and processing
│   │   ├── models/                  # YOLO model weights
│   │   │   ├── pothole.pt
│   │   │   ├── trash.pt
│   │   │   └── trash_new.pt
│   │   ├── criticality_score.py
│   │   ├── final.py
│   │   ├── impact.py
│   │   ├── pothole_agent.py
│   │   └── trash_agent1.py
│   └── utils/
├── uploads/
├── tests/
├── main.py
├── requirements.txt
└── database_schema.sql
```

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t urban-watch-api .

# Run container
docker run -p 8000:8000 --env-file .env urban-watch-api
```

### Production Considerations
- Set strong `SECRET_KEY` in production
- Configure CORS properly for your frontend domain
- Use HTTPS for all endpoints
- Set up proper logging and monitoring
- Configure Redis persistence
- Use a CDN for image serving
- Set up database backups

## 📈 Monitoring

The API includes health check endpoints:
- `GET /` - Basic API info
- `GET /health` - Health status

Monitor these endpoints for service availability.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please:
1. Check the troubleshooting section below
2. Review the API documentation at `/docs`
3. Open an issue on the repository

## 🔍 Troubleshooting

### Common Issues

#### "Redis connection failed"
- Ensure Redis server is running
- Check `REDIS_URL` in `.env` file
- Verify Redis is accessible

#### "Supabase authentication failed"
- Check Supabase credentials in `.env`
- Verify Supabase project is active
- Ensure database tables are created

#### "AI model not found"
- Check if model files exist in `app/ai/models/`
- Ensure proper file permissions
- Models are optional - API works without them

#### "Import errors"
- Run `python setup.py` to install dependencies
- Activate virtual environment if using one
- Check Python version (3.8+ required)

### Logs
Application logs are written to console. In production, configure proper log aggregation.

## 📋 Roadmap

- [ ] WebSocket support for real-time updates
- [ ] Push notifications for report status changes
- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] Mobile app integration improvements
- [ ] Performance optimizations
- [ ] Additional AI models for more issue types
