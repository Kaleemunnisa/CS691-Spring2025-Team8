# 🛒 PaceCart: Advancing Grocery E-Commerce with Sequential Pattern Mining and Deep Learning

> **CS 691 – Spring 2025 Capstone Project**

---

## 📘 Introduction

PaceCart is a personalized grocery e-commerce platform that enhances the shopping experience by delivering **smart, adaptive product recommendations**. It uses a combination of **High Utility Sequential Pattern Mining (HUSPM)**, **deep learning**, **collaborative filtering**, and **content-based filtering** to provide each user with personalized grocery suggestions based on behavior, utility, trends, and sequence of purchases.

---

## 🚨 Problem Statement

Traditional online grocery platforms offer generic, one-size-fits-all suggestions. Users waste time navigating irrelevant items, and platforms fail to account for **personal preferences**, **utility value**, and **sequential purchase behavior**. There is a clear need for an intelligent system that personalizes grocery shopping.

---

## ✅ Solution Overview

PaceCart tackles this by:
- Tracking and analyzing each user’s browsing and purchase behavior.
- Using HUSPM and hybrid models to generate utility-based recommendations.
- Displaying personalized, score-driven suggestions on the homepage and recommendation page.

The platform provides a smooth grocery browsing and checkout experience with an elegant UI, while a powerful backend engine computes relevant product suggestions.

---

## 🔑 Key Features

### 🧠 AI-Powered Recommendations
- Uses **HUSPM** to understand item utility and purchase sequences.
- Incorporates **Deep Learning** (TensorFlow/Keras) to refine utility scores.
- Combines **Collaborative & Content-Based Filtering** for fallback recommendations.

### 🛒 Full Grocery Platform
- Browse items by category: Snacks, Beverages, Fruits, Vegetables, Dairy, etc.
- Add to cart, update quantity, and checkout easily.
- Rate purchased items and view order history.

### 🎯 Personalization
- Tracks user activity: purchases, browsing, clicks.
- Shows recommendations with **source** (e.g., HUSPM) and **score**.
- Suggests trending items and “recently viewed” products.

### 💎 Frontend UI/UX
- Modern pastel-themed UI with TailwindCSS
- Fully responsive across devices
- Features animated buttons, sliders, category dropdowns, and flash messages
  ![image](https://github.com/user-attachments/assets/219c1d95-9cfe-4ab1-a1b3-cbd076db1160)
  ![image](https://github.com/user-attachments/assets/1819b910-efdf-4101-95c0-d3e8d667043d)
  ![image](https://github.com/user-attachments/assets/5b898ce2-b875-481d-990b-f3158e857cc6)

---

## 🏗️ Technology Stack

| Layer             | Technology                             |
|------------------|-----------------------------------------|
| Frontend         | HTML, CSS, Tailwind, JS, Jinja2         |
| Backend          | Python Flask                            |
| Database         | MySQL                                   |
| AI Models        | TensorFlow, Pandas, NumPy               |
| Recommendation   | HUSPM, Collaborative, Content-Based     |
| Hosting (local)  | Gunicorn + NGINX                        |
| Design/Mockups   | Figma                                   |

---

## ⚙️ Installation Guide

```bash
git clone https://github.com/yourusername/pacecart.git
cd pacecart/backend
pip install -r requirements.txt
```

### 💾 MySQL Setup

```sql
CREATE DATABASE pacecart_data;
```

> Import your schema and product data using seed_data.py or a .sql script

Update `db_connection.py` with:

```python
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="yourpassword",
    database="pacecart_data"
)
```

---

## 🧪 Run the App

```bash
python app.py
```

Visit: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 📂 Directory Structure (simplified)

```
pacecart/
├── backend/
│   ├── app.py
│   ├── db_connection.py
│   ├── models/
│   ├── huspm_module/
│   ├── templates/
│   ├── static/
│   └── seed_data.py
├── requirements.txt
└── README.md
```

---

## 📌 Sample Routes

| Route                             | Description                          |
|-----------------------------------|--------------------------------------|
| `/`                               | Landing page                         |
| `/login`, `/signup`               | User authentication                  |
| `/home`                           | Main homepage                        |
| `/cart`                           | View and update cart                 |
| `/recommendations/<user_id>`      | Personalized recommendations         |
| `/order-history`                  | View rated order history             |
|`/all_products`                    | Paginated list of all products (48 per page)        |
| `/recommendations/<user_id>`      | Personalized recommendations from DB                |
| `/category/<category_name>`       | Filter products by category                         |
| `/product_details/<product_id>`   | Detailed view of a single product (optional page) 
---

## 🎯 Expected Outcomes

- Save time by recommending only relevant products.
- Improve user satisfaction with smarter suggestions.
- Showcase value of HUSPM in a real-world retail platform.
- Deliver a modern, scalable e-commerce solution.

---

## 📃 License

This project is licensed under the [MIT License](LICENSE).


---
