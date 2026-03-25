document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('generate-btn');
    const loader = document.getElementById('loader');
    const ballsContainer = document.getElementById('balls-container');
    const algoInfo = document.getElementById('algo-info');
    
    // Hide loader initially
    loader.classList.add('hidden');

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
});
