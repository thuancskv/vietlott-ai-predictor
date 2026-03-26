document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('generate-btn');
    const loader = document.getElementById('loader');
    const ballsContainer = document.getElementById('balls-container');
    const algoInfo = document.getElementById('algo-info');
    
    // Modal Elements
    const infoModal = document.getElementById('info-modal');
    const infoBtn = document.getElementById('info-btn');
    const closeBtn = document.querySelector('.close-btn');

    // Hide loader initially
    loader.classList.add('hidden');

    // --- Latest Info Logic ---
    let latestData = null;

    async function updateLatestInfo() {
        const gameType = document.getElementById('game-type').value;
        const jackpotElem = document.getElementById('current-jackpot');
        const drawDetailsElem = document.getElementById('draw-details');
        const lastBallsElem = document.getElementById('last-draw-balls');
        const titleElem = document.getElementById('current-game-title');

        if (!latestData) {
            try {
                const response = await fetch('/api/latest_info');
                const data = await response.json();
                if (data.success) {
                    latestData = data;
                }
            } catch (err) {
                console.error("Failed to fetch latest info", err);
            }
        }

        if (latestData) {
            const info = gameType === 'mega' ? latestData.mega : latestData.power;
            titleElem.innerHTML = `<i class="fas fa-trophy" style="color: gold;"></i> Thông tin ${gameType === 'mega' ? 'Mega 6/45' : 'Power 6/55'}`;
            if (gameType === 'power' && info.prize.includes('|')) {
                const parts = info.prize.split('|');
                // Use smaller font for J1/J2 split
                jackpotElem.innerHTML = `<div style="font-size: 0.75em; margin-bottom: 5px; color: #ffeb3b;">${parts[0].trim()}</div>` + 
                                       `<div style="font-size: 0.75em; color: #fff;">${parts[1].trim()}</div>`;
            } else {
                jackpotElem.innerText = info.prize;
            }
            drawDetailsElem.innerText = `Kỳ #${info.draw_id} ngày ${info.draw_date}`;
            
            lastBallsElem.innerHTML = '';
            if (info.last_draw && info.last_draw.length > 0) {
                info.last_draw.forEach((num, idx) => {
                    const b = document.createElement('div');
                    b.className = 'ball-s';
                    // Special styling for the 7th ball in Power 6/55
                    if (gameType === 'power' && idx === 6) {
                        b.style.background = 'radial-gradient(circle at 30% 30%, #ffeb3b, #fbc02d)';
                        b.style.color = '#000';
                        b.style.borderColor = '#f9a825';
                    }
                    b.innerText = num < 10 ? '0' + num : num;
                    lastBallsElem.appendChild(b);
                });
            } else {
                lastBallsElem.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem;">Chưa có dữ liệu</div>';
            }
        }
    }

    // Initial load
    updateLatestInfo();

    // Update on game change
    document.getElementById('game-type').addEventListener('change', updateLatestInfo);
    // --- End Latest Info Logic ---

    btn.addEventListener('click', async () => {
        // UI Reset
        ballsContainer.innerHTML = '';
        ballsContainer.classList.add('hidden');
        algoInfo.classList.add('hidden');
        loader.classList.remove('hidden');
        btn.disabled = true;
        
        const gameType = document.getElementById('game-type').value;
        const algoType = document.getElementById('algo-type').value;

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    game_type: gameType,
                    algo_type: algoType
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Determine algo name for display
                const algoSelect = document.getElementById('algo-type');
                const algoName = algoSelect.options[algoSelect.selectedIndex].text;
                
                setTimeout(() => renderBalls(data.prediction, algoName), 800);
            } else {
                alert('Lỗi khi phân tích dữ liệu: ' + data.error);
                loader.classList.add('hidden');
                btn.disabled = false;
            }
        } catch (err) {
            console.error(err);
            alert('Lỗi kết nối đến máy chủ AI.');
            loader.classList.add('hidden');
            btn.disabled = false;
        }
    });

    function renderBalls(numbers, algoName) {
        loader.classList.add('hidden');
        ballsContainer.classList.remove('hidden');
        
        numbers.forEach((num, index) => {
            const ball = document.createElement('div');
            ball.className = 'ball';
            // pad single digits
            ball.innerText = num < 10 ? '0' + num : num;
            // stagger animation
            ball.style.animationDelay = `${index * 0.15}s`;
            ballsContainer.appendChild(ball);
        });
        
        algoInfo.innerHTML = `Kết quả tính toán với thuật toán: <b style="color:white;">${algoName}</b>`;
        algoInfo.classList.remove('hidden');
        btn.disabled = false;
    }

    // Modal Logic
    infoBtn.addEventListener('click', () => {
        infoModal.classList.remove('hidden');
    });

    closeBtn.addEventListener('click', () => {
        infoModal.classList.add('hidden');
    });

    window.addEventListener('click', (e) => {
        if (e.target === infoModal) {
            infoModal.classList.add('hidden');
        }
    });
});
