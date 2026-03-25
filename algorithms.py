import random
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from collections import defaultdict

def get_historical_data(conn, game_type):
    query = f"SELECT n1, n2, n3, n4, n5, n6 FROM draws WHERE game_type = '{game_type}' ORDER BY id ASC"
    df = pd.read_sql_query(query, conn)
    return df

def get_max_num(game_type):
    # Accept various identifiers for the game type
    lower = game_type.lower()
    if 'mega' in lower:
        return 45
    elif 'power' in lower:
        return 55
    else:
        # Default fallback to 45 for safety
        return 45

def fetch_flat_history(df):
    nums = []
    for _, row in df.iterrows():
        nums.extend([row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']])
    return nums

# 1. Frequency Analysis (Hot/Cold)
def predict_frequency(df, max_num, strategy="hot"):
    nums = fetch_flat_history(df)
    counts = {i: 0 for i in range(1, max_num + 1)}
    for n in nums:
        if 1 <= n <= max_num:
            counts[n] += 1
        
    sorted_nums = sorted(counts.items(), key=lambda item: item[1], reverse=(strategy == "hot"))
    pool = [n for n, c in sorted_nums[:15]]  # take top 15
    
    # Ensure there's a fallback if pool is somehow very small
    selected = random.sample(pool, min(6, len(pool)))
    while len(selected) < 6:
        selected.append(random.randint(1, max_num))
        
    return sorted(list(set(selected)))[:6]

# 2. Delta System
def predict_delta(df, max_num):
    # Calculate typical deltas
    deltas = []
    for _, row in df.iterrows():
        draw = sorted([row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']])
        draw_deltas = [draw[0]] + [draw[i] - draw[i-1] for i in range(1, 6)]
        deltas.append(draw_deltas)
        
    # Sample common deltas
    avg_deltas = np.median(deltas, axis=0).astype(int)
    
    # Reconstruct
    res = [avg_deltas[0]]
    for i in range(1, 6):
        next_val = res[-1] + avg_deltas[i]
        # Add some jitter to make it unique
        jitter = random.randint(-2, 2)
        next_val += jitter
        while next_val in res or next_val > max_num or next_val < 1:
            next_val = random.randint(1, max_num)
        res.append(next_val)
    return sorted(res)

# 3. Markov Chain
def predict_markov(df, max_num):
    transitions = defaultdict(lambda: defaultdict(int))
    nums = fetch_flat_history(df)
    
    for i in range(len(nums) - 1):
        transitions[nums[i]][nums[i+1]] += 1
        
    # Start with a random number
    current = random.randint(1, max_num)
    res = set([current])
    
    while len(res) < 6:
        if current in transitions and transitions[current]:
            # Weighted choice
            choices = list(transitions[current].keys())
            weights = list(transitions[current].values())
            current = random.choices(choices, weights=weights)[0]
        else:
            current = random.randint(1, max_num)
        
        res.add(current)
        
    return sorted(list(res))

# 4. K-Means Clustering (Unsupervised ML)
def predict_kmeans(df, max_num):
    if len(df) < 10:
        return predict_frequency(df, max_num)
    
    X = df.values
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    kmeans.fit(X)
    
    # Pick a random center
    center = random.choice(kmeans.cluster_centers_)
    # Add random noise to center
    res = set()
    for val in center:
        num = int(round(val)) + random.randint(-3, 3)
        while num in res or num < 1 or num > max_num:
            num = random.randint(1, max_num)
        res.add(num)
        if len(res) == 6:
            break
            
    while len(res) < 6:
        num = random.randint(1, max_num)
        res.add(num)
            
    return sorted(list(res))

# 5. Random Forest (Supervised ML)
def predict_random_forest(df, max_num):
    if len(df) < 20:
        return predict_frequency(df, max_num)
        
    X = []
    y = []
    # Create sliding windows: use last 3 draws to predict next draw
    window_size = 3
    for i in range(len(df) - window_size):
        window = df.iloc[i:i+window_size].values.flatten()
        target = df.iloc[i+window_size].values
        X.append(window)
        # For simplicity, target is just the first number of the next draw
        y.append(target[0])
        
    rf = RandomForestClassifier(n_estimators=50, random_state=42)
    rf.fit(X, y)
    
    latest_window = df.iloc[-window_size:].values.flatten()
    pred_first = rf.predict([latest_window])[0]
    
    res = set([int(pred_first)])
    while len(res) < 6:
        n = random.randint(1, max_num)
        res.add(n)
        
    return sorted(list(res))

# 6. Genetic Algorithm
def predict_genetic(df, max_num):
    def fitness(ticket):
        # Fitness based on spreading of numbers (avoiding all sequential)
        # and sum being in average range
        score = 0
        total = sum(ticket)
        # Average sum of 6 numbers out of 45 is approx 138
        if 100 <= total <= 180:
            score += 10
        # Check even/odd ratio
        evens = sum(1 for n in ticket if n % 2 == 0)
        if 2 <= evens <= 4:
            score += 10
        return score

    # Generate population
    pop_size = 100
    population = [sorted(random.sample(range(1, max_num + 1), 6)) for _ in range(pop_size)]
    
    # Evolve a few generations
    for _ in range(10):
        # Grade
        graded = [(fitness(t), t) for t in population]
        graded = [x[1] for x in sorted(graded, key=lambda x: x[0], reverse=True)]
        
        # Keep top 20%
        retain_length = int(len(graded) * 0.2)
        parents = graded[:retain_length]
        
        # Mutate
        for p in parents:
            if random.random() < 0.1:
                idx = random.randint(0, 5)
                new_val = random.randint(1, max_num)
                if new_val not in p:
                    p[idx] = new_val
                    p.sort()
                    
        # Crossover
        parents_length = len(parents)
        desired_length = len(population) - parents_length
        children = []
        while len(children) < desired_length:
            male = random.randint(0, parents_length-1)
            female = random.randint(0, parents_length-1)
            if male != female:
                male = parents[male]
                female = parents[female]
                half = int(len(male) / 2)
                child = set(male[:half] + female[half:])
                # Fill missing if duplicates
                while len(child) < 6:
                    child.add(random.randint(1, max_num))
                children.append(sorted(list(child))[:6])
        
        population = parents + children
        
    return population[0]

def get_prediction(conn, game_type, algo_type="ensemble"):
    df = get_historical_data(conn, game_type)
    max_num = get_max_num(game_type)
    
    if len(df) == 0:
        # Fallback random
        return sorted(random.sample(range(1, max_num + 1), 6))
        
    if algo_type == "frequency_hot":
        return predict_frequency(df, max_num, "hot")
    elif algo_type == "frequency_cold":
        return predict_frequency(df, max_num, "cold")
    elif algo_type == "delta":
        return predict_delta(df, max_num)
    elif algo_type == "markov":
        return predict_markov(df, max_num)
    elif algo_type == "kmeans":
        return predict_kmeans(df, max_num)
    elif algo_type == "random_forest":
        return predict_random_forest(df, max_num)
    elif algo_type == "genetic":
        return predict_genetic(df, max_num)
    else:
        # Ensemble: run all and pick most common
        all_preds = []
        all_preds.extend(predict_frequency(df, max_num, "hot"))
        all_preds.extend(predict_delta(df, max_num))
        all_preds.extend(predict_markov(df, max_num))
        all_preds.extend(predict_kmeans(df, max_num))
        all_preds.extend(predict_genetic(df, max_num))
        
        counts = {i: 0 for i in range(1, max_num + 1)}
        for p in all_preds:
            p_int = int(p)
            if 1 <= p_int <= max_num:
                counts[p_int] += 1
            
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ensemble_res = [x[0] for x in sorted_counts[:6]]
        return sorted(ensemble_res)
