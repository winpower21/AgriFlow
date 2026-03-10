# AgriFlow 🌾

AgriFlow is a professional, full-stack Agricultural Management System (Farm ERP) designed to streamline farm operations. From tracking personnel and plantations to managing inventory, expenses, and vehicle fleets, AgriFlow provides a centralized platform for modern agricultural enterprises.

## 🚀 Overview

AgriFlow bridges the gap between field operations and administrative management. It offers real-time insights into crop cycles, inventory levels, and financial performance, integrated with live weather data to aid decision-making.

---

## ✨ Features

### 👤 Personnel Management
- **Staff Profiles:** Track farm workers, roles, and contact information.
- **Photo Uploads:** Secure storage and retrieval of personnel identification photos.
- **RBAC:** Built-in Role-Based Access Control (Admin, Manager, User).

### 🌱 Plantation & Crop Tracking
- **Field Management:** Detailed records of plantations, locations, and soil conditions.
- **Batch Traceability:** Full "Seed-to-Retail" genealogy tracking. Follow a product from harvest through cleaning, drying, and grading to the final retail batch.
- **Transformation Logs:** Record every processing stage (e.g., HARVEST -> CLEAN -> DRY -> BAG -> GRADE).

### 📦 Inventory & Consumables
- **Stock Tracking:** Real-time monitoring of seeds, fertilizers, pesticides, and other supplies.
- **Purchase History:** Detailed logs of consumable acquisitions linked to financial expenses.

### 💰 Financial Management
- **Expense Tracking:** Categorized logging of operational costs.
- **Integrated Purchasing:** Automatically link consumable purchases to expense reports for accurate P&L analysis.

### 🚜 Vehicle & Fleet Management
- **Asset Tracking:** Monitor farm machinery, vehicles, and maintenance schedules.
- **Usage Logs:** Track fuel consumption and operational hours (extensible).

### 🌤️ Weather Integration
- **Real-time Data:** Integration with OpenWeatherMap for current field conditions.
- **Location-based Insights:** Geocoding via Google Maps API for precise plantation weather monitoring.

### ⚖️ Approval Workflow
- **Request System:** Formalize internal requests for inventory, expenses, or operational changes with a multi-level approval system.

---

## 🛠️ Tech Stack

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Database:** [PostgreSQL 17](https://www.postgresql.org/)
- **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
- **Security:** JWT (HS256) via `python-jose`, password hashing via `bcrypt`.
- **Validation:** [Pydantic v2](https://docs.pydantic.dev/)

### Frontend
- **Framework:** [Vue.js 3](https://vuejs.org/) (Composition API)
- **Build Tool:** [Vite](https://vitejs.dev/)
- **State Management:** [Pinia](https://pinia.vuejs.org/)
- **Routing:** [Vue Router](https://router.vuejs.org/)
- **Styling:** [Bootstrap 5](https://getbootstrap.com/) & [Bootstrap Icons](https://icons.getbootstrap.com/)
- **HTTP Client:** [Axios](https://axios-http.com/)

### DevOps & Infrastructure
- **Containerization:** [Docker](https://www.docker.com/) & Docker Compose
- **Static Files:** FastAPI `StaticFiles` for serving uploads.

---

## 📂 Project Structure

```text
AgriFlow/
├── backend/                # FastAPI Application
│   ├── app/
│   │   ├── api/            # External API integrations (Weather/Google)
│   │   ├── core/           # Security and dependencies
│   │   ├── crud/           # Business logic / DB interactions
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── routers/        # API endpoints (FastAPI APIRouter)
│   │   ├── schemas/        # Pydantic models (Request/Response)
│   │   └── main.py         # App entry point & configuration
│   ├── alembic/            # DB Migration scripts
│   └── uploads/            # Root for static file uploads
├── frontend/               # Vue.js 3 Application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── stores/         # Pinia state management
│   │   ├── utils/          # API/Axios configuration
│   │   └── views/          # Page-level components
│   └── public/             # Static assets
└── docker-compose.yaml     # Orchestration for DB and Backend
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL (or Docker)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/AgriFlow.git
cd AgriFlow
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:
```env
DATABASE_URL=postgresql+psycopg://myuser:mypassword@localhost:5432/mydb
SECRET_KEY=your_super_secret_key_here
ALLOWED_ORIGINS=http://localhost:5173
ENVIRONMENT=development
OPENWEATHERMAP_API_KEY=your_key
GOOGLE_MAPS_API_KEY=your_key
```

Run migrations:
```bash
alembic upgrade head
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

### 4. Running with Docker (Recommended)
```bash
docker-compose up --build
```
*The backend will be available at `http://localhost:8000` and the DB on `5432`.*

---

## 📖 Usage Guide

1. **First Run:** The system automatically seeds default roles (`admin`, `manager`, `user`) on the first startup.
2. **Authentication:** Register a new account. The first registered user can be manually promoted to `admin` in the database to access user management.
3. **Dashboard:** View high-level metrics across all modules.
4. **API Documentation:** Visit `http://localhost:8000/api/docs` for the interactive Swagger UI.

---

## 🔐 Security Considerations
- **JWT Authentication:** Tokens are used for all protected routes.
- **Password Hashing:** Uses `bcrypt` for secure storage.
- **CORS:** Configured via `ALLOWED_ORIGINS` to prevent unauthorized cross-origin requests.
- **RBAC:** Metadata-driven role verification on both frontend (router guards) and backend (dependencies).

---

## 🚧 Roadmap & Future Improvements
- [ ] **Mobile App:** Flutter or React Native companion for field data entry.
- [ ] **IoT Integration:** Soil moisture and temperature sensors for automated plantation monitoring.
- [ ] **AI Forecasting:** Yield prediction based on historical data and weather patterns.
- [ ] **Offline Support:** PWA capabilities for use in remote areas with poor connectivity.
- [ ] **Advanced Reporting:** Exportable PDF/Excel reports for financial auditing.

---

## 🤝 Contributing
Contributions are welcome! Please follow these steps:
1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

## ✍️ Author
**Lakshya Luv Mimani** - *Lead Developer* - [GitHub](https://github.com/winpower21)
