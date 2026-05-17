"""
一个极简的文学人格测试网站
使用 Flask 框架实现
"""
from flask import Flask, request, render_template_string, session, redirect, url_for
import os

# --- 初始化 Flask 应用 ---
app = Flask(__name__)
# session 加密需要的一串随机字符，用于在用户浏览器和服务器间安全传递信息
app.secret_key = os.urandom(24)

# ==========================================
# ① 核心数据：授权码库 和 测试题库
# ==========================================
# 字典：键是授权码，值是布尔值（True表示未被使用，False表示已用过）
VALID_CODES = {
    "ABC123": True,
    "XYZ789": True,
    "LIT456": True,
    "QWE777": True,
    "ART888": True,
    "POE999": True,
    "SHA555": True,
    "DAN222": True,
    "AUS333": True,
    "TOL444": True,
}

# 测试题目列表。每道题是一个字典，包含题目、选项，以及每个选项对应的分数
QUESTIONS = [
    {
        "question": "1. 在聚会上，你通常？",
        "options": [
            ("A. 独自在角落观察人群，构思他们的故事", 3),  # 内省型
            ("B. 和每个人都能聊上几句，像一条游动的鱼", 1), # 交际型
            ("C. 和一两个好友进行深入灵魂的交谈", 2)       # 深度型
        ]
    },
    {
        "question": "2. 哪种描述更贴近你对命运的看法？",
        "options": [
            ("A. 我命由我不由天，人是自由的", 1),
            ("B. 一切冥冥中自有注定，我们只是演员", 3),
            ("C. 命运是随机而荒诞的，毫无逻辑可言", 2)
        ]
    },
    {
        "question": "3. 写作或创作时，你最看重什么？",
        "options": [
            ("A. 结构的精巧与形式的完美", 1),
            ("B. 情绪的饱满与灵魂的震颤", 3),
            ("C. 思想的锋利与对现实的批判", 2)
        ]
    }
]

# 结果映射：根据总分范围，显示不同的文学人格
# 总分最小3分（全选A），最大9分（全选B）
RESULTS = {
    (7, 9): {
        "title": "🕯️ 孤独的浪漫主义者 — 局外人/诗人型",
        "desc": "你的灵魂与梅尔索、维特深深共鸣。你敏感而疏离，在热闹中渴望孤独，在孤独中却创造出一个丰饶的精神世界。你相信真实高于一切，哪怕这真实是痛苦的。"
    },
    (5, 6): {
        "title": "📖 清醒的批判者 — 知识分子/哲人型",
        "desc": "你像黑塞笔下的荒原狼，或鲁迅笔下的过客。你无法停止思考，对社会与人性的痼疾有着锐利的洞察。你愤怒、你探寻，只因你对这片土地爱得深沉。"
    },
    (3, 4): {
        "title": "✨ 生命的舞者 — 行动者/体验派",
        "desc": "你充满澎湃的生命力，像《飘》中的郝思嘉，或海明威笔下的硬汉。你相信行动的力量，即使明天是世界末日，今天你也要种下自己的苹果树。"
    }
}

# ==========================================
# ② 页面样式：用 CSS 让网站看起来简洁文艺
# ==========================================
BASE_STYLE = """
<style>
    body {
        font-family: 'Georgia', 'Times New Roman', serif;
        background-color: #fdfaf6;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        margin: 0;
        padding: 20px;
        color: #4a3f35;
    }
    .container {
        background: white;
        padding: 40px 50px;
        border-radius: 2px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        max-width: 500px;
        width: 100%;
        border: 1px solid #e8e0d5;
    }
    h1 {
        font-weight: normal;
        text-align: center;
        font-size: 28px;
        letter-spacing: 4px;
        margin-bottom: 30px;
        color: #5a4e3c;
    }
    input[type="text"], button {
        width: 100%;
        padding: 12px;
        margin: 10px 0;
        border: 1px solid #d4c9b5;
        border-radius: 2px;
        box-sizing: border-box;
        font-family: inherit;
        font-size: 16px;
    }
    button {
        background-color: #5a4e3c;
        color: white;
        cursor: pointer;
        transition: background-color 0.3s;
        border: none;
    }
    button:hover {
        background-color: #3d3428;
    }
    .question-block {
        margin-bottom: 30px;
    }
    .question-block p {
        font-style: italic;
        margin-bottom: 12px;
    }
    label {
        display: block;
        padding: 10px 0;
        cursor: pointer;
        border-bottom: 1px dotted #e8e0d5;
    }
    label:hover {
        background-color: #fcfaf5;
    }
    .error {
        color: #b85c5c;
        text-align: center;
        margin-top: 10px;
    }
    .result-title {
        font-size: 22px;
        text-align: center;
        margin: 20px 0;
        line-height: 1.4;
    }
    .result-desc {
        font-style: italic;
        line-height: 1.8;
        text-align: justify;
    }
    .small-note {
        text-align: center;
        font-size: 12px;
        color: #a09588;
        margin-top: 20px;
    }
</style>
"""

# ==========================================
# ③ 页面模板（HTML骨架）
# ==========================================
# 首页：输入授权码
HOME_PAGE = BASE_STYLE + """
<div class="container">
    <h1>LITERA<br><span style="font-size:14px; letter-spacing:2px;">文学人格原型测试</span></h1>
    <form method="POST" action="{{ url_for('verify') }}">
        <input type="text" name="code" placeholder="请输入你的6位专属授权码" required maxlength="6" autocomplete="off">
        <button type="submit">开启测试</button>
    </form>
    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}
    <p class="small-note">一个授权码仅限使用一次</p>
</div>
"""

# 测试题页面
TEST_PAGE = BASE_STYLE + """
<div class="container">
    <h1>LITERA</h1>
    <form method="POST" action="{{ url_for('result') }}">
        {% for q in questions %}
        <div class="question-block">
            <p>{{ q.question }}</p>
            {% for option_text, option_score in q.options %}
            <label>
                <input type="radio" name="q{{ loop.index0 }}" value="{{ option_score }}" required> 
                {{ option_text }}
            </label>
            {% endfor %}
        </div>
        {% endfor %}
        <button type="submit">查看我的文学人格</button>
    </form>
</div>
"""

# 结果页面
RESULT_PAGE = BASE_STYLE + """
<div class="container">
    <h1>LITERA</h1>
    <div class="result-title">{{ result.title }}</div>
    <div class="result-desc">{{ result.desc }}</div>
    <p class="small-note" style="margin-top:30px;">感谢参与，每个灵魂都是一部未完成的手稿。</p>
</div>
"""

# ==========================================
# ④ 路由（网站的不同“门”）
# ==========================================
@app.route('/')
def home():
    """首页，显示输入框"""
    return render_template_string(HOME_PAGE)

@app.route('/verify', methods=['POST'])
def verify():
    """验证授权码"""
    code = request.form.get('code', '').strip().upper()  # 获取用户输入并转为大写
    
    # 检查1：长度必须为6
    if len(code) != 6:
        return render_template_string(HOME_PAGE, error="授权码必须为6位字符。")
    
    # 检查2：是否在有效码字典中 且 未被使用
    if code not in VALID_CODES:
        return render_template_string(HOME_PAGE, error="无效的授权码。")
    
    if not VALID_CODES[code]:
        return render_template_string(HOME_PAGE, error="该授权码已被使用。")
    
    # 验证通过！标记此码为已使用
    VALID_CODES[code] = False
    # 在用户会话中标记其已通过验证
    session['authenticated'] = True
    session['current_code'] = code  # 记录使用的码（可选，用于后续逻辑）
    
    # 重定向到测试页面
    return redirect(url_for('test'))

@app.route('/test')
def test():
    """测试页面，需要验证通过才能访问"""
    if not session.get('authenticated'):
        return redirect(url_for('home'))
    return render_template_string(TEST_PAGE, questions=QUESTIONS)

@app.route('/result', methods=['POST'])
def result():
    """结果页面，计算得分并显示人格"""
    if not session.get('authenticated'):
        return redirect(url_for('home'))
    
    # 计算总分
    total_score = 0
    for i in range(len(QUESTIONS)):
        # 获取每道题选中选项的分数（radio的值）
        score_str = request.form.get(f'q{i}')
        if score_str:
            total_score += int(score_str)
    
    # 根据总分区间找到对应的人格结果
    user_result = None
    for (low, high), result_data in RESULTS.items():
        if low <= total_score <= high:
            user_result = result_data
            break
    
    # 如果没有匹配（极端情况），给一个默认结果
    if not user_result:
        user_result = {
            "title": "📜 未分类的独行者",
            "desc": "你是一个复杂的混合体，难以被简单定义。也许这正是你最迷人的特质。"
        }
    
    # 清除会话，允许用户关闭页面后授权码即失效（或保留，根据你的需求）
    # 这里选择不清除，但如果用户想重用同一设备，需要重新输入码。
    # 更严格的做法是 session.clear()
    
    return render_template_string(RESULT_PAGE, result=user_result)

# ==========================================
# ⑤ 启动网站
# ==========================================
if __name__ == '__main__':
    # debug=True 表示开启调试模式，代码修改后服务器会自动重启，方便测试
    # 实际部署到线上时需要关闭 debug
    app.run(debug=True)