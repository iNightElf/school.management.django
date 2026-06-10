import json
import random
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


STUB_QUIZZES = [
    {
        "question": "What is the largest ocean on Earth?",
        "option_a": "Atlantic Ocean",
        "option_b": "Indian Ocean",
        "option_c": "Pacific Ocean",
        "option_d": "Arctic Ocean",
        "correct_answer": "c",
        "category": "general",
        "explanation": "The Pacific Ocean covers about 63 million square miles, making it the largest ocean on Earth.",
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "option_a": "Venus",
        "option_b": "Mars",
        "option_c": "Jupiter",
        "option_d": "Saturn",
        "correct_answer": "b",
        "category": "science",
        "explanation": "Mars appears red due to iron oxide (rust) on its surface.",
    },
    {
        "question": "Who painted the Mona Lisa?",
        "option_a": "Vincent van Gogh",
        "option_b": "Pablo Picasso",
        "option_c": "Leonardo da Vinci",
        "option_d": "Michelangelo",
        "correct_answer": "c",
        "category": "general",
        "explanation": "Leonardo da Vinci painted the Mona Lisa between 1503 and 1519.",
    },
    {
        "question": "What is the chemical symbol for water?",
        "option_a": "H2O",
        "option_b": "CO2",
        "option_c": "NaCl",
        "option_d": "O2",
        "correct_answer": "a",
        "category": "science",
        "explanation": "Water is composed of two hydrogen atoms and one oxygen atom (H2O).",
    },
    {
        "question": "In which year did World War II end?",
        "option_a": "1943",
        "option_b": "1944",
        "option_c": "1945",
        "option_d": "1946",
        "correct_answer": "c",
        "category": "history",
        "explanation": "World War II ended in 1945 with the surrender of Japan in September.",
    },
    {
        "question": "What is the square root of 144?",
        "option_a": "10",
        "option_b": "11",
        "option_c": "12",
        "option_d": "14",
        "correct_answer": "c",
        "category": "math",
        "explanation": "12 x 12 = 144, so the square root of 144 is 12.",
    },
    {
        "question": "Which continent has the most countries?",
        "option_a": "Asia",
        "option_b": "Europe",
        "option_c": "Africa",
        "option_d": "South America",
        "correct_answer": "c",
        "category": "geography",
        "explanation": "Africa has 54 recognized countries, more than any other continent.",
    },
    {
        "question": "What gas do plants absorb from the atmosphere?",
        "option_a": "Oxygen",
        "option_b": "Nitrogen",
        "option_c": "Carbon Dioxide",
        "option_d": "Hydrogen",
        "correct_answer": "c",
        "category": "science",
        "explanation": "Plants absorb carbon dioxide (CO2) during photosynthesis to produce glucose and oxygen.",
    },
    {
        "question": "Who wrote Romeo and Juliet?",
        "option_a": "Charles Dickens",
        "option_b": "William Shakespeare",
        "option_c": "Jane Austen",
        "option_d": "Mark Twain",
        "correct_answer": "b",
        "category": "literature",
        "explanation": "William Shakespeare wrote Romeo and Juliet around 1594-1596.",
    },
    {
        "question": "How many sides does a hexagon have?",
        "option_a": "5",
        "option_b": "6",
        "option_c": "7",
        "option_d": "8",
        "correct_answer": "b",
        "category": "math",
        "explanation": "A hexagon is a polygon with 6 sides.",
    },
]

STUB_RIDDLES = [
    {
        "question": "I speak without a mouth and hear without ears. I have no body, but I come alive with the wind. What am I?",
        "hint": "Think about what happens when sound bounces off surfaces.",
        "answer": "echo",
    },
    {
        "question": "The more you take, the more you leave behind. What am I?",
        "hint": "Think about movement and traces.",
        "answer": "footsteps",
    },
    {
        "question": "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?",
        "hint": "You might find me on a wall or in a classroom.",
        "answer": "map",
    },
    {
        "question": "What gets wetter the more it dries?",
        "hint": "You use me after a shower or washing dishes.",
        "answer": "towel",
    },
    {
        "question": "I have keys but no locks. I have space but no room. You can enter but can't go inside. What am I?",
        "hint": "You're using one right now to read this.",
        "answer": "keyboard",
    },
    {
        "question": "What can travel around the world while staying in a corner?",
        "hint": "You put me on an envelope.",
        "answer": "stamp",
    },
    {
        "question": "I have a head and a tail but no body. What am I?",
        "hint": "Flip me to decide something.",
        "answer": "coin",
    },
    {
        "question": "What comes once in a minute, twice in a moment, but never in a thousand years?",
        "hint": "Look at the letters in the words themselves.",
        "answer": "the letter m",
    },
]

STUB_TIPS = {
    'classroom': [
        "Start each class with a 2-minute attention grabber: a question, a short story, or a surprising fact. It sets the tone for focused learning.",
        "Establish clear routines for entering class, turning in work, and asking for help. Predictability reduces anxiety and misbehavior.",
        "Use proximity strategically — moving closer to distracted students often redirects behavior without words.",
    ],
    'assessment': [
        "Use exit tickets at the end of class to quickly gauge understanding. Even a sticky note with 'What did you learn?' gives valuable data.",
        "Mix formative assessments: whiteboards, think-pair-share, one-minute papers. variety keeps students engaged and gives different insights.",
        "When grading, look for patterns in errors rather than just marking wrong answers. Patterns reveal what needs reteaching.",
    ],
    'engagement': [
        "Give students choice when possible — choice of topic, format, or partner. Autonomy increases motivation.",
        "Connect lessons to students' lives and interests. The question 'When will I use this?' should have a clear answer.",
        "Use strategic pair work. Partner a strong student with a struggling one for mutual benefit.",
    ],
    'general': [
        "Take 5 minutes each evening to plan tomorrow's key actions. A clear plan reduces decision fatigue.",
        "Celebrate small wins daily — a student's improvement, a successful lesson, a kind gesture. Positivity compounds.",
        "Build relationships with colleagues. A quick coffee chat or shared resource can transform your day.",
    ],
}

STUB_CHALLENGES = [
    {
        "title": "Gratitude Wall",
        "description": "Write one thing you're grateful for about your school, students, or teaching career this week.",
        "challenge_type": "text",
    },
    {
        "title": "Rate Your Week",
        "description": "How was your teaching week? Tap the emoji that best describes it!",
        "challenge_type": "emoji",
    },
    {
        "title": "Share a Win",
        "description": "Describe one small victory from this week — a student breakthrough, a lesson that clicked, or anything that went well.",
        "challenge_type": "text",
    },
    {
        "title": "Photo Challenge",
        "description": "Share a photo of your workspace, classroom, or something that inspires you to teach.",
        "challenge_type": "text",
    },
    {
        "title": "Learning Goal",
        "description": "What is one thing you want to learn or improve as a teacher this month?",
        "challenge_type": "text",
    },
]


def _call_gemini(prompt):
    """Call Google Gemini API via REST. Returns response text or None on failure."""
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return None
    try:
        import urllib.request
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-2.0-flash:generateContent?key={api_key}"
        )
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.warning(f"Gemini API error: {e}")
        return None


def _parse_json_response(text):
    """Extract JSON from AI response text."""
    if not text:
        return None
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1] if '\n' in text else text[3:]
        text = text.rsplit('```', 1)[0]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return None


def generate_quiz(category='general'):
    """Generate a quiz question using AI or stub."""
    prompt = (
        f"Generate a multiple-choice quiz question for school teachers. "
        f"Category: {category}. "
        f"Return ONLY valid JSON: "
        f'{{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", '
        f'"correct_answer": "a", "explanation": "..."}}. '
        f"Make it interesting but not too difficult."
    )
    response_text = _call_gemini(prompt)
    data = _parse_json_response(response_text)
    if data and all(k in data for k in ('question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer')):
        data['category'] = category
        return data, 'ai'

    stub = random.choice(STUB_QUIZZES)
    return stub, 'stub'


def generate_riddle():
    """Generate a riddle using AI or stub."""
    prompt = (
        "Create a clever riddle that teachers would enjoy. "
        'Return ONLY valid JSON: {"question": "...", "hint": "...", "answer": "..."}. '
        "The riddle should be tricky but fair."
    )
    response_text = _call_gemini(prompt)
    data = _parse_json_response(response_text)
    if data and all(k in data for k in ('question', 'answer')):
        data.setdefault('hint', '')
        return data, 'ai'

    stub = random.choice(STUB_RIDDLES)
    return stub, 'stub'


def generate_tip(category='general'):
    """Generate a teaching tip using AI or stub."""
    prompt = (
        f"Give one practical teaching tip about {category}. "
        f"Keep it under 2 sentences. Be specific and actionable."
    )
    response_text = _call_gemini(prompt)
    if response_text and len(response_text.strip()) > 10:
        return response_text.strip(), 'ai'

    tips = STUB_TIPS.get(category, STUB_TIPS['general'])
    return random.choice(tips), 'stub'


def generate_challenge():
    """Generate a weekly challenge using AI or stub."""
    prompt = (
        "Create a fun weekly challenge for school teachers. "
        'Return ONLY valid JSON: {"title": "...", "description": "...", "challenge_type": "text"}. '
        "Make it engaging and easy to participate in."
    )
    response_text = _call_gemini(prompt)
    data = _parse_json_response(response_text)
    if data and all(k in data for k in ('title', 'description')):
        data.setdefault('challenge_type', 'text')
        return data, 'ai'

    stub = random.choice(STUB_CHALLENGES)
    return stub, 'stub'
