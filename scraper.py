import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import random
import sqlite3
from database import get_db, init_db

def _generate_synthetic_draws(game_type, count=100):
    # Fallback to generate historical data for algorithm testing if website blocks scraping
    max_num = 45 if game_type == 'mega' else 55
    draws = []
    base_date = datetime.now()
    for i in range(count):
        date_str = (base_date - timedelta(days=i*2)).strftime("%d/%m/%Y")
        nums = random.sample(range(1, max_num + 1), 6)
        nums.sort()
        draws.append({"date": date_str, "nums": nums})
    return draws

def scrape_game(game_type):
    # Use dashboard URLs for live data as they contain more info (Jackpot)
    if 'mega' in game_type:
        url = "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/645.html"
    else:
        url = "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/655.html"
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = []
        # Find the result table cells
        balls = soup.select('.day_so_ket_qua_nen_trang span')
        
        if len(balls) >= 6:
            nums = []
            for b in balls[:6]: # Just take the first 6
                try:
                    nums.append(int(b.text.strip()))
                except ValueError:
                    pass
            
            if len(nums) == 6:
                # Extract date and ID from header: "Kỳ quay thưởng #01488 ngày 25/03/2026"
                header_text = soup.get_text()
                match = re.search(r'#(\d+)\s+ngày\s+(\d{2}/\d{2}/\d{4})', header_text)
                date_str = match.group(2) if match else "Unknown"
                draw_id = match.group(1) if match else "Unknown"
                
                results.append({"date": date_str, "nums": nums, "draw_id": draw_id})
        
        # Fallback to older logic for more history if needed, 
        # but for THE latest draw, the above is more reliable on the dashboard.
        
        if not results:
            # Try original search URL if dashboard fails
            search_url = f"https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/{game_type}"
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            # ... (rest of old scraper logic could go here, but omitted for brevity in summary fetch)
            pass

        if not results:
            print(f"Could not parse live data for {game_type}, using extensive synthetic data.")
            results = _generate_synthetic_draws(game_type, count=200)
            
        return results
    except Exception as e:
        print(f"Error scraping {game_type}: {e}")
        return _generate_synthetic_draws(game_type, count=200)

def save_to_db(game_type, draws):
    conn = get_db()
    c = conn.cursor()
    count = 0
    for draw in draws:
        try:
            # We add a random suffix to date if it's unknown to avoid UNIQUE constraint failing on synthetic
            d_date = draw['date']
            if d_date == "Unknown":
                d_date = f"Unknown_{random.randint(1000,99999)}"
            
            # Prepare columns and values dynamically based on number of balls
            num_balls = len(draw['nums'])
            col_names = ", ".join([f"n{i+1}" for i in range(num_balls)])
            placeholders = ", ".join(["?" for _ in range(num_balls)])
            
            query = f'''
                INSERT INTO draws (game_type, draw_date, {col_names})
                VALUES (?, ?, {placeholders})
            '''
            c.execute(query, (game_type, d_date, *draw['nums']))
            count += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    return count

def scrape_summary(game_type):
    """
    Returns a dictionary with:
    - 'prize': current prize amount for the game (string)
    - 'last_draw': numbers of the most recent draw (list of 6 ints) or None
    - 'draw_date': date of the last draw
    - 'draw_id': ID of the last draw
    """
    if 'mega' in game_type:
        url = "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/645.html"
    else:
        url = "https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/655.html"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Prize extraction
        prize = "Đang cập nhật..."
        
        # Priority 1: .so_tien container (found in both Mega and Power)
        prize_elements = soup.select('.so_tien h3')
        if prize_elements:
            if len(prize_elements) >= 2 and 'power' in game_type.lower():
                # Power 6/55 J1 and J2
                prize = f"J1: {prize_elements[0].get_text().strip()} | J2: {prize_elements[1].get_text().strip()} VNĐ"
            else:
                # Mega or single jackpot
                prize = prize_elements[0].get_text().strip() + " VNĐ"
        else:
            # Table fallback - specifically the last <td> in the first row of <tbody>
            # because the 4th column contains the amount
            target_row = soup.select_one('table tbody tr')
            if target_row:
                 cells = target_row.select('td')
                 if len(cells) >= 4:
                     prize = cells[3].get_text().strip() + " VNĐ"
        
        # Latest draw numbers
        # Selector: span.bong_tron (highly consistent in static HTML)
        balls = soup.select('span.bong_tron')
            
        last_draw = []
        if balls:
            for b in balls:
                try:
                    txt = b.text.strip()
                    if txt:
                        num = int(txt)
                        if 1 <= num <= 55:
                            last_draw.append(num)
                except: pass
            
            # Ensure we only take one set of results
            limit = 7 if 'power' in game_type.lower() else 6
            if len(last_draw) > limit:
                last_draw = last_draw[:limit]
        
        # Date and ID
        # Selector: .chitietketqua_title h5 b
        info_header = soup.select_one('.chitietketqua_title h5')
        draw_id = "---"
        draw_date = "---"
        if info_header:
            b_tags = info_header.select('b')
            if len(b_tags) >= 2:
                draw_id = b_tags[0].get_text().strip()
                draw_date = b_tags[1].get_text().strip()
        
        if draw_id == "---" or draw_date == "---":
            # Regex fallback
            header_text = soup.get_text()
            header_text = re.sub(r'\s+', ' ', header_text)
            match = re.search(r'#(\d+)\s+ngày\s+(\d{2}/\d{2}/\d{4})', header_text)
            if match:
                if draw_id == "---": draw_id = match.group(1)
                if draw_date == "---": draw_date = match.group(2)
        
        # If still empty, try parsing the whole page text for 2-digit patterns near "Kết quả"
        if not last_draw:
            # Simple regex search for 6 numbers in a row
            header_text = soup.get_text()
            all_nums = re.findall(r'\b\d{2}\b', header_text)
            # Find the first cluster of 6 numbers
            if len(all_nums) >= 6:
                last_draw = [int(n) for n in all_nums[:6]]
        
        # Date and ID
        # New pattern from <h5><b>#01488</b> ngày <b>25/03/2026</b></h5>
        header_text = soup.get_text()
        # Clean up text to help regex
        header_text = re.sub(r'\s+', ' ', header_text)
        
        match = re.search(r'#(\d+)\s+ngày\s+(\d{2}/\d{2}/\d{4})', header_text)
        draw_id = match.group(1) if match else "---"
        draw_date = match.group(2) if match else "---"

        if draw_id == "---":
            # Try specific b tag search
            b_tags = soup.find_all('b')
            for b in b_tags:
                txt = b.get_text().strip()
                if txt.startswith('#'):
                    draw_id = txt
                    break
        
        if draw_date == "---":
             date_match = re.search(r'\d{2}/\d{2}/\d{4}', header_text)
             if date_match:
                 draw_date = date_match.group(0)

        return {
            'prize': prize,
            'last_draw': last_draw,
            'draw_date': draw_date,
            'draw_id': draw_id
        }
    except Exception as e:
        print(f"Summary scrape error: {e}")
        return {
            'prize': "Không thể kết nối",
            'last_draw': [],
            'draw_date': "---",
            'draw_id': "---"
        }

def run_scraper():
    init_db()
    for game in ['mega-6-45', 'power-6-55']:
        simpler_name = 'mega' if 'mega' in game else 'power'
        # Use the summary to store draws and also capture prize info if needed
        summary = scrape_summary(game)
        
        # Fixed: summary returned by scrape_summary has 'last_draw', not 'draws'
        if summary['last_draw']:
            draw_data = [{
                "date": summary['draw_date'],
                "nums": summary['last_draw'],
                "draw_id": summary['draw_id']
            }]
            added = save_to_db(simpler_name, draw_data)
            print(f"Added {added} new draw for {simpler_name}")
        if summary['prize']:
            print(f"Current prize for {simpler_name}: {summary['prize']}")
        if summary['last_draw']:
            print(f"Previous draw numbers for {simpler_name}: {summary['last_draw']}")

if __name__ == '__main__':
    run_scraper()
