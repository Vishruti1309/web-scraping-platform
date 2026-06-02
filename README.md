🚀 Job Tracker & Web Scraping Dashboard

A full-stack **AI-inspired web scraping and job tracking platform** that extracts data from websites, processes it, stores it in a database, and provides an interactive dashboard with filtering, sorting, and save features.

This project combines **Web Scraping + ETL Pipeline + Full-Stack Dashboard**, making it a real-world data engineering + frontend system.



🌟 Key Features

 🔍 Smart Web Scraping Engine

* Multi-page scraping (pagination support)
* Supports static websites (BooksToScrape)
* Easily extendable to job platforms (RemoteOK, Internshala)
* Retry logic and structured extraction



 ⚙️ Data Processing Pipeline (ETL)

* Data cleaning (whitespace, formatting)
* Field standardization (`field_mapping`)
* Duplicate removal
* Validation & filtering
* Ready for analytics



 🗄️ Database Layer (SQLite)

* Stores all scraped data
* Maintains scraping history
* Supports saved/bookmarked jobs 



 📤 Export System

Automatically exports data into:

* CSV
* JSON
* Excel

Stored inside `/exports/` folder.



 📊 React Dashboard (Frontend)

Interactive UI with:

* 🔍 Search functionality
* 💰 Price (salary) filter
* 🔄 Sort toggle (Newest / Oldest)
* 📊 Results count
* ❤️ Save job feature
* 🧹 Clear data functionality



 ❤️ Save / Bookmark Feature

* Save selected items to database
* Separate storage (`saved_jobs` table)
* Mimics real job platforms (LinkedIn / Indeed)



 🧠 Monitoring & Logging

* Scraping logs
* Error tracking
* Performance monitoring
* Job history tracking



🏗️ Tech Stack

🔹 Backend

* FastAPI
* Python
* SQLite
* Pandas

🔹 Frontend

* React (Vite)
* Axios
* Inline CSS (custom UI)

🔹 Scraping

* Requests / BeautifulSoup
* Playwright / Selenium (extendable)



📂 Project Structure

```
scraping_system/
│── scraper_engine.py
│── data_processor.py
│── storage_manager.py
│── scheduler_orchestrator.py
│── api_server.py
│── config.py
│
├── frontend/          → React app
├── data/              → SQLite DB
├── exports/           → CSV/JSON/Excel
├── logs/              → Logs
```



⚙️ Installation & Setup

 1️⃣ Clone Repository

```bash
git clone https://github.com/Vishruti1309/web-scraping-platform
cd project-name
```



 2️⃣ Backend Setup

```bash
pip install -r requirements.txt
uvicorn api_server:app --reload
```

Backend runs on:

```
http://127.0.0.1:8000
```



 3️⃣ Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on:

```
http://localhost:5173
```



▶️ How It Works

```
User clicks "Start Scraping"
        ↓
Scraper Engine fetches data
        ↓
Data Processor cleans & standardizes
        ↓
StorageManager saves to DB
        ↓
Exporter creates CSV/JSON/Excel
        ↓
React Dashboard displays data
        ↓
User can filter / sort / save 
```



📸 Features Demo (Add screenshots here)

* Dashboard UI - [Dashboard](screenshot/dashboard.png)
* Filters & sorting - [Filters](screenshot/filtering%20&%20sorting.png)
* Exported files - [Exported_files](exports/books_data_20260601_184449.csv)



🚀 Future Improvements

* 🌍 Real job scraping (RemoteOK, Internshala)
* 🔐 User authentication
* ☁️ Deployment (Vercel + Render)
* 📱 Responsive UI
* 🔔 Notifications / alerts



🧠 What This Project Demonstrates

* Full-stack development (React + FastAPI)
* Web scraping architecture
* ETL pipeline design
* Database handling
* API integration
* UI/UX thinking



📌 Conclusion

This project is not just a scraper — it is a **complete data pipeline + dashboard system** that mimics real-world job platforms and data engineering workflows.
