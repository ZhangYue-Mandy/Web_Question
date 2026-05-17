"""
一个极简的文学人格测试网站
使用 Flask 框架实现
"""
from flask import Flask, request, render_template_string, session, redirect, url_for
import os
import json

# 记录已使用授权码的文件路径
USED_CODES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'used_codes.json')

# --- 初始化 Flask 应用 ---
app = Flask(__name__)
# session 加密需要的一串随机字符，用于在用户浏览器和服务器间安全传递信息
app.secret_key = os.urandom(24)

# ==========================================
# ① 核心数据：授权码库 和 测试题库
# ==========================================
# 字典：键是授权码，值是布尔值（True表示未被使用，False表示已用过）
# 管理员万能码：永远有效，不消耗
ADMIN_CODE = "ADMIN0"
# 管理员后台密码
ADMIN_PASSWORD = "mmlzy123"  # 改成你自己的
VALID_CODES = [
    "ABC123",
    "XYZ789",
    "LIT456",
    "QWE777",
    "ART888",
    "POE999",
    "SHA555",
    "DAN222",
    "AUS333",
    "TOL444",
]

def load_used_codes():
    """从文件读取已使用的授权码集合"""
    try:
        with open(USED_CODES_FILE, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_used_code(code):
    """将一个授权码追加到已使用文件"""
    used = load_used_codes()
    used.add(code)
    with open(USED_CODES_FILE, 'w') as f:
        json.dump(list(used), f)

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
                <input type="radio" name="q{{ questions.index(q) }}" value="{{ option_score }}" required> 
                {{ option_text }}
            </label>
            {% endfor %}
        </div>
        {% endfor %}
        <button type="submit">查看我的文学人格</button>
    </form>
</div>
"""
# 管理员后台页面
ADMIN_PAGE = BASE_STYLE + """
<div class="container">
    <h1>LITERA · 管理后台</h1>
    <div style="margin-bottom:20px; padding:15px; background:#f9f6f0; border-radius:2px;">
        <h3 style="margin-top:0;">📊 授权码状态</h3>
        <table style="width:100%; border-collapse:collapse;">
            <tr style="border-bottom:1px solid #d4c9b5;">
                <th style="padding:8px; text-align:left;">授权码</th>
                <th style="padding:8px; text-align:center;">状态</th>
                <th style="padding:8px; text-align:center;">操作</th>
            </tr>
            {% for info in code_list %}
            <tr style="border-bottom:1px dotted #e8e0d5;">
                <td style="padding:8px;">{{ info.code }}</td>
                <td style="padding:8px; text-align:center;">
                    {% if info.used %}
                    <span style="color:#b85c5c;">已使用</span>
                    {% else %}
                    <span style="color:#6a9a6a;">可用</span>
                    {% endif %}
                </td>
                <td style="padding:8px; text-align:center;">
                    {% if info.used %}
                    <a href="?action=reset_one&code={{ info.code }}" style="color:#5a4e3c;">重置</a>
                    {% else %}
                    -
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <div style="margin-bottom:20px;">
        <a href="?action=reset_all" style="display:inline-block; padding:10px 20px; background:#b85c5c; color:white; text-decoration:none; border-radius:2px; margin-right:10px;" 
           onclick="return confirm('确定要重置所有授权码吗？');">全部重置</a>
    </div>
    
    <div style="padding:15px; background:#f9f6f0; border-radius:2px;">
        <h3 style="margin-top:0;">➕ 添加新授权码</h3>
        <form method="GET" action="">
            <input type="hidden" name="action" value="add_code">
            <input type="text" name="new_code" placeholder="输入6位新授权码" required maxlength="6" style="width:70%; padding:10px; border:1px solid #d4c9b5; border-radius:2px;">
            <button type="submit" style="width:25%; padding:10px;">添加</button>
        </form>
        {% if msg %}
        <p style="color:#6a9a6a; margin-top:10px;">{{ msg }}</p>
        {% endif %}
    </div>
    
    <p class="small-note" style="margin-top:20px;"><a href="{{ url_for('home') }}">返回首页</a></p>
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
    
       # 检查0：管理员万能码，永久有效，不消耗
    if code == ADMIN_CODE:
        session['authenticated'] = True
        session['current_code'] = code
        return redirect(url_for('test'))
    
    # 检查1：长度必须为6
    if len(code) != 6:
        return render_template_string(HOME_PAGE, error="授权码必须为6位字符。")
    
    # 检查2：是否在有效码列表中
    if code not in VALID_CODES:
        return render_template_string(HOME_PAGE, error="无效的授权码。")
    
    # 检查3：是否已被使用
    used_codes = load_used_codes()
    if code in used_codes:
        return render_template_string(HOME_PAGE, error="该授权码已被使用。")
    
    # 验证通过！将此码记录为已使用
    save_used_code(code)

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
    # 显示结果后立即清除会话，刷新页面就会回到首页
    session.clear()
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

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """管理员后台（需密码）"""
    # 如果还没登录，显示密码输入页
    if not session.get('is_admin'):
        if request.method == 'POST':
            pwd = request.form.get('password', '')
            if pwd == ADMIN_PASSWORD:
                session['is_admin'] = True
            else:
                return render_template_string(BASE_STYLE + """
                <div class="container">
                    <h1>LITERA · 后台</h1>
                    <form method="POST">
                        <input type="password" name="password" placeholder="请输入管理密码" required>
                        <button type="submit">登录</button>
                    </form>
                    <p class="error">密码错误</p>
                </div>
                """)
        else:
            return render_template_string(BASE_STYLE + """
            <div class="container">
                <h1>LITERA · 后台</h1>
                <form method="POST">
                    <input type="password" name="password" placeholder="请输入管理密码" required>
                    <button type="submit">登录</button>
                </form>
            </div>
            """)
    
    # 已登录，处理操作
    msg = None
    action = request.args.get('action', '')
    
    if action == 'reset_all':
        # 全部重置
        with open(USED_CODES_FILE, 'w') as f:
            json.dump([], f)
        msg = "所有授权码已重置。"
    
    elif action == 'reset_one':
        # 重置单个码
        code_to_reset = request.args.get('code', '').upper()
        used = load_used_codes()
        if code_to_reset in used:
            used.remove(code_to_reset)
            with open(USED_CODES_FILE, 'w') as f:
                json.dump(list(used), f)
            msg = f"授权码 {code_to_reset} 已重置为可用。"
    
    elif action == 'add_code':
        # 添加新码
        new_code = request.args.get('new_code', '').strip().upper()
        if len(new_code) == 6:
            # 加入到有效码列表（存在 used_codes.json 的空集合里，表示未使用）
            # 同时要加到内存的 VALID_CODES 里
            if new_code not in VALID_CODES:
                VALID_CODES.append(new_code)
            # 从已使用集合中移除（如果存在的话）
            used = load_used_codes()
            if new_code in used:
                used.remove(new_code)
                with open(USED_CODES_FILE, 'w') as f:
                    json.dump(list(used), f)
            msg = f"新授权码 {new_code} 已添加，立即可用。"
        else:
            msg = "授权码必须为6位字符。"
    
    # 构建码状态列表
    used_codes = load_used_codes()
    code_list = []
    for c in VALID_CODES:
        code_list.append({
            'code': c,
            'used': c in used_codes
        })
    
    return render_template_string(ADMIN_PAGE, code_list=code_list, msg=msg)
# ==========================================
# ⑤ 启动网站
# ==========================================
if __name__ == '__main__':
    # debug=True 表示开启调试模式，代码修改后服务器会自动重启，方便测试
    # 实际部署到线上时需要关闭 debug
    app.run(debug=True)