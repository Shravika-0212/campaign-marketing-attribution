# Fresher's Guide: Marketing Attribution & ROI Analytics Platform
> **Made for Interviews & Clear Understanding**  
> *Written in simple, everyday English so you can understand every concept and confidently explain it to any interviewer.*

---

## 1. What is this project in one simple sentence?

> **"This project is a website and data engine that tracks how people see company ads, click links, and eventually buy products, so the company knows exactly which ads made money and which ads wasted money."**

---

## 2. The Real-Life Story (Understand the Problem in 2 Minutes)

Imagine you want to buy a new smartphone. Here is what you do:

1. **Day 1:** You are scrolling on Instagram and see an ad for a new phone called *FlexPhone*. You click it, look at the picture, and leave. *(Touchpoint 1: Paid Social)*
2. **Day 15:** You search on Google: "Best battery phones 2026". You click an article on their website and download a brochure with your email. *(Touchpoint 2: Organic Search & Lead Form)*
3. **Day 30:** They send you an email with a 10% discount code. You click the email link and buy the phone for **$1,000**. *(Touchpoint 3: Email Marketing & Order)*

### The Big Question:
Who gets the credit for that $1,000 sale?
- Was it the **Instagram Ad**? (Without it, you would never have heard of the phone!)
- Was it the **Google Search**? (That's where you learned about the features!)
- Was it the **Email with the coupon**? (That's the exact link you used to pay!)

If the company gives 100% of the credit to the Email, they might stop spending money on Instagram! But if they stop Instagram, new people will never find out about the phone!

This is called **Marketing Attribution**. Our project solves this puzzle by mathematically comparing different ways to share the credit.

---

## 3. The Three Ways to Share Credit (Attribution Models)

Our platform calculates 3 models:

| Model Name | How It Works in Plain Words | Example on a $1,000 Order | When is it useful? |
| :--- | :--- | :--- | :--- |
| **1. First-Touch** | Gives **100% credit** to the very first ad the person ever clicked. | Instagram Ad gets **$1,000**. Google gets $0. Email gets $0. | When you want to see which ads are best at bringing in **new brand awareness**. |
| **2. Last-Touch** | Gives **100% credit** to the last ad clicked before buying. | Email gets **$1,000**. Instagram gets $0. Google gets $0. | When you want to see which ads are best at **closing deals and getting money**. |
| **3. Multi-Touch (Linear)** | Gives **equal credit** to all the ads the customer saw. | 3 touches $\rightarrow$ each gets $1/3$ ($33.3\%$). Instagram: **$333.33$**, Google: **$333.33$**, Email: **$333.34$**. | When you want a **fair, balanced view** of the whole team effort. |

Notice that in Multi-Touch, $333.33 + 333.33 + 333.34 = 1,000.00$. The total credit is always **exactly 100%**!

---

## 4. The 5 Real-World Data Traps We Catch (Anomalies)

In real companies, data is never clean. People make mistakes and computer systems glitch. Our project has an automated "Security Guard" (Anomaly Detector) that catches 5 specific traps:

### 1. Duplicate Revenue (Double-Counting Money)
- **The Problem:** A computer glitch saves the exact same order twice. A $1,000 order suddenly looks like $2,000!
- **Our Fix:** We check order numbers. If we see the same order twice, we quarantine the second one and only count $1,000.

### 2. Touchpoint After Conversion (Time Travel Bug)
- **The Problem:** Someone bought the phone on Friday, but clicked a help-center ad on Saturday. An ad engine might mistakenly claim that Saturday's click caused Friday's purchase! That is impossible.
- **Our Fix:** We check timestamps. Any click that happened *after* the purchase date is kicked out of attribution.

### 3. Currency Mismatch (Mixing Apples and Oranges)
- **The Problem:** An ad in Germany spent €5,000 Euros, but our system budget is in US Dollars ($). If you add 5,000 Euros to 5,000 Dollars without converting, your math is wrong!
- **Our Fix:** We flag any non-USD currency and separate it until a verified exchange rate is provided.

### 4. Missing Campaign Cost (Free Ad Illusion)
- **The Problem:** A campaign made $50,000 in sales, but someone forgot to upload the bill for the ads. If you calculate `ROI = (Revenue - Cost) / Cost`, you have to divide by zero! That crashes computers, or makes the ad look infinitely profitable.
- **Our Fix:** We detect missing costs, prevent division by zero, and mark the ROI as "Unavailable - Missing Cost".

### 5. Unsupported Identity Links (Guessing Who Visited)
- **The Problem:** An anonymous visitor visits the website. A system guesses "Oh, that must be John!" without any cookie or email proof.
- **Our Fix:** If there is no real cookie or email match in our identity table, we quarantine the link so we don't attribute revenue to the wrong person.

---

## 5. What Did I Actually Build? (The 6 Building Blocks)

If an interviewer asks: *"Walk me through the architecture of what you built,"* tell them these 6 steps:

```
[1. Database (SQLite)] 
       ↓
[2. Data Generator (Python)] 
       ↓
[3. Attribution Engine] 
       ↓
[4. Financial & ROI Engine] 
       ↓
[5. Anomaly Detection & 15 Rules Validator] 
       ↓
[6. Web Dashboard (React + TypeScript + Tailwind)]
```

1. **The Relational Database:**
   - We created 12 main tables (Channels, Campaigns, Creatives, Audiences, Contacts, Sessions, Touchpoints, Leads, Opportunities, Orders, Cost Records, and Attribution Results).
   - Foreign keys connect them together so every order links back to a contact and a campaign.

2. **The Data Generator:**
   - Because we don't have real customer data, we wrote a Python program that generates realistic customer journeys.
   - We used a fixed seed (`20261022`). This means if you run the program 10 times, you get the exact same numbers every single time. It is 100% reproducible.

3. **The Attribution Engine:**
   - Wrote Python code that takes all customer touches, filters out any touch older than 90 days or after the purchase, and calculates First-Touch, Last-Touch, and Multi-Touch credits.

4. **The Financial & ROI Engine:**
   - Calculates Campaign Spend, Closed Revenue, and ROI:  
     $$\text{ROI} = \left(\frac{\text{Revenue} - \text{Cost}}{\text{Cost}}\right) \times 100$$
   - Calculates Cost Per Lead (CPL) and Cost Per Acquisition (CPA).

5. **The Anomaly Detector & Validator:**
   - Wrote rules to catch the 5 traps.
   - Evaluated our detector against a separate "Ground Truth" file and proved it achieved **100% Precision and 100% Recall**.
   - Ran 15 automated validation checks across 23,000+ records.

6. **The Frontend Web Dashboard:**
   - Built a modern, clean web dashboard using React, TypeScript, and Tailwind CSS.
   - 8 pages with charts, interactive tables, customer journey timelines, and download buttons.

---

## 6. How to Run It on Your Computer (3 Easy Commands)

### Step 1: Open your terminal inside the folder
```bash
cd yottaflex-marketing-attribution
```

### Step 2: Run the automated data generation and test pipeline
```bash
python backend/scripts/generate_and_run_all.py
```
*(In less than 2 seconds, it resets the database, creates the tables, generates thousands of records, calculates attribution, catches anomalies, and exports CSV/JSON files!)*

### Step 3: Start the server and open the web app
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Now open your web browser and go to:
👉 **`http://localhost:8000`**

You will see the live, working dashboard with all numbers, charts, and tables!

---

## 7. How to Ace Your Technical Interview (Cheat Sheet)

### Q1: "Tell me about this project."
> *"I built an end-to-end Marketing Attribution and ROI Analytics Platform in Python and React. It tracks the complete customer journey from the first ad impression through leads and opportunities to final purchase orders. It allows marketing teams to compare First-Touch, Last-Touch, and Multi-Touch attribution models, while automatically detecting data quality anomalies like duplicate revenue or touchpoints recorded after conversion."*

### Q2: "Why did you use SQLite and FastAPI instead of a heavy cloud setup?"
> *"I chose FastAPI and SQLite with Write-Ahead Logging (WAL) and foreign keys enabled because it requires zero paid cloud services, has zero setup hassle, and runs blazingly fast locally. The entire starter dataset generates in just 1.2 seconds, and the backend has 22 automated tests that pass in 13 seconds."*

### Q3: "What is Ground Truth, and why did you keep it separate?"
> *"Ground truth is our answer key—it lists the exact anomalies we deliberately injected so we can test our detector. In machine learning and data engineering, you must never let the answer key leak into your detection features, otherwise the computer is just cheating! We keep ground truth in a separate file and only look at it at the end to calculate Precision, Recall, and F1 score."*

### Q4: "How did you handle division by zero in ROI?"
> *"If a campaign has zero recorded spend, the formula `(Revenue - Cost) / Cost` would divide by zero and crash. Instead of assuming zero cost means infinite profit, my engine flags the campaign with status `UNAVAILABLE_MISSING_COST`, sets ROI to null, and alerts the team that cost data is missing."*

### Q5: "How do you ensure reproducibility?"
> *"I initialized Python's random number generator with a fixed seed (`20261022`). If you run the generator twice on any computer, it generates the exact same row counts and produces the exact same SHA-256 cryptographic checksums."*
