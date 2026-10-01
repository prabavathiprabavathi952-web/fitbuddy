"""Rule-based 7-day plan builder. Used when Gemini is unavailable so the app never breaks."""
from app.nutrition import goal_category

WARMUPS = {
    "full": "Jumping jacks, world's greatest stretch, bodyweight squats, cat-cow",
    "upper": "Arm circles, band pull-aparts or scapular push-ups, 10 slow push-ups, shoulder rolls",
    "lower": "Hip circles, leg swings, bodyweight squats, glute bridges",
    "cardio": "3-5 min brisk walk or easy jog, high knees, butt kicks, dynamic lunges",
    "core": "Cat-cow, bird-dogs, dead bugs, glute bridges",
    "mobility": "Easy walk, neck and shoulder rolls, hip circles, thoracic rotations",
}
COOLDOWNS = {
    "full": "Slow walk for 3 min, then stretch quads, hamstrings, chest and back (30 sec each)",
    "upper": "Hold chest, shoulder, triceps and lat stretches for 30 seconds each",
    "lower": "Hold quad, hamstring, calf and hip-flexor stretches for 30-45 seconds each",
    "cardio": "Walk until your heart rate settles, then stretch calves, quads and hips",
    "core": "Child's pose, cobra stretch and gentle spinal twists, 1 min each",
    "mobility": "Box breathing for 2 minutes and a relaxed full-body stretch",
}

# Each session: (title, type, [(exercise, prescription)]). {s} is replaced by the set count.
SESSIONS = {
    "fat_loss": [
        ("Full-body strength circuit", "full", [
            ("Goblet squat", "{s} x 12"), ("Push-ups", "{s} x 10-15"),
            ("One-arm dumbbell row", "{s} x 12 each side"),
            ("Dumbbell Romanian deadlift", "{s} x 12"), ("Plank", "{s} x 30-45 sec")]),
        ("Interval cardio", "cardio", [
            ("Intervals: 30 sec hard / 60 sec easy on a bike, jog or rowing machine", "8 rounds"),
            ("Mountain climbers", "{s} x 30 sec"), ("Jump rope or high knees", "{s} x 45 sec")]),
        ("Lower body and core", "lower", [
            ("Reverse lunges", "{s} x 12 each leg"), ("Glute bridges", "{s} x 15"),
            ("Dumbbell step-ups", "{s} x 10 each leg"), ("Bicycle crunches", "{s} x 20"),
            ("Dead bug", "{s} x 10 each side")]),
        ("Upper body and core", "upper", [
            ("Dumbbell shoulder press", "{s} x 10-12"), ("Incline push-ups", "{s} x 12-15"),
            ("Bent-over dumbbell row", "{s} x 12"), ("Triceps dips (bench)", "{s} x 10-12"),
            ("Plank shoulder taps", "{s} x 20")]),
        ("Steady-state cardio", "cardio", [
            ("Zone-2 cardio (brisk walk, cycle or swim; you can still hold a conversation)", "30-40 min"),
            ("Bodyweight squats", "{s} x 15")]),
        ("Full-body power circuit", "full", [
            ("Dumbbell swings", "{s} x 15"), ("Burpees (step back if needed)", "{s} x 8-10"),
            ("Walking lunges", "{s} x 20 steps"), ("Push-up to shoulder tap", "{s} x 10"),
            ("Russian twists", "{s} x 20")]),
    ],
    "muscle": [
        ("Push: chest, shoulders, triceps", "upper", [
            ("Dumbbell or barbell bench press", "{s} x 8-10"), ("Incline dumbbell press", "{s} x 8-12"),
            ("Overhead press", "{s} x 8-10"), ("Lateral raises", "{s} x 12-15"),
            ("Triceps pushdowns or dips", "{s} x 10-12")]),
        ("Pull: back and biceps", "upper", [
            ("Pull-ups or lat pulldowns", "{s} x 6-10"), ("Barbell or dumbbell row", "{s} x 8-10"),
            ("Seated cable row", "{s} x 10-12"), ("Face pulls", "{s} x 15"),
            ("Dumbbell biceps curls", "{s} x 10-12")]),
        ("Legs and glutes", "lower", [
            ("Barbell or goblet squat", "{s} x 8-10"), ("Romanian deadlift", "{s} x 8-10"),
            ("Walking lunges", "{s} x 12 each leg"), ("Hip thrusts", "{s} x 10-12"),
            ("Standing calf raises", "{s} x 15")]),
        ("Upper body (volume)", "upper", [
            ("Incline push-ups or machine press", "{s} x 12"), ("One-arm dumbbell row", "{s} x 12"),
            ("Arnold press", "{s} x 10-12"), ("Hammer curls", "{s} x 12"),
            ("Overhead triceps extension", "{s} x 12")]),
        ("Lower body (volume) and core", "lower", [
            ("Front squat or leg press", "{s} x 10-12"), ("Bulgarian split squat", "{s} x 10 each leg"),
            ("Leg curls or good mornings", "{s} x 12"), ("Hanging knee raises", "{s} x 12"),
            ("Plank", "{s} x 45-60 sec")]),
        ("Full body and conditioning", "full", [
            ("Deadlift or kettlebell deadlift", "{s} x 6-8"), ("Push press", "{s} x 8"),
            ("Chin-ups or inverted rows", "{s} x 8-10"), ("Farmer's carry", "{s} x 40 m"),
            ("Ab wheel or dead bug", "{s} x 10")]),
    ],
    "general": [
        ("Full-body strength", "full", [
            ("Bodyweight or goblet squat", "{s} x 12"), ("Push-ups (or knee push-ups)", "{s} x 8-12"),
            ("Dumbbell row", "{s} x 12"), ("Glute bridges", "{s} x 15"), ("Plank", "{s} x 30 sec")]),
        ("Cardio and endurance", "cardio", [
            ("Brisk walk, jog or cycle at a comfortable pace", "25-35 min"),
            ("Jumping jacks", "{s} x 30 sec")]),
        ("Mobility and yoga flow", "mobility", [
            ("Sun salutation flow", "5 rounds"), ("Cat-cow", "{s} x 10"),
            ("Low lunge with rotation", "{s} x 8 each side"), ("Downward dog to child's pose", "{s} x 8"),
            ("Seated forward fold", "{s} x 45 sec")]),
        ("Upper body and core", "upper", [
            ("Dumbbell shoulder press", "{s} x 10"), ("Incline push-ups", "{s} x 10-12"),
            ("Band pull-aparts", "{s} x 15"), ("Bird-dog", "{s} x 10 each side"),
            ("Side plank", "{s} x 20-30 sec each side")]),
        ("Lower body and balance", "lower", [
            ("Step-ups", "{s} x 10 each leg"), ("Reverse lunges", "{s} x 10 each leg"),
            ("Single-leg balance hold", "{s} x 30 sec each leg"), ("Calf raises", "{s} x 15"),
            ("Wall sit", "{s} x 30-45 sec")]),
        ("Active fun", "cardio", [
            ("Sport, hike, swim, dance or cycle: anything you enjoy", "40-60 min"),
            ("Full-body stretch", "10 min")]),
    ],
}

# Which day numbers are training days (True) for each intensity.
SCHEDULE = {
    "low":    [True, False, True, False, True, False, True],
    "medium": [True, True, False, True, True, False, True],
    "high":   [True, True, True, False, True, True, True],
}
SETS = {"low": 2, "medium": 3, "high": 4}
REST = {"low": "60-90 sec", "medium": "45-75 sec", "high": "30-60 sec"}
LABEL = {"fat_loss": "Fat Loss", "muscle": "Muscle Gain", "general": "General Fitness"}
EXPERIENCE_NOTE = {
    "beginner": "Start with light weights and focus on clean form before adding load.",
    "intermediate": "Add weight or a rep whenever you finish every set with good form.",
    "advanced": "Use a slow 3-second lowering phase on the last set of each exercise to raise the challenge.",
}


def build_offline_plan(u: dict) -> str:
    goal = u.get("goal", "general fitness")
    intensity = u.get("intensity", "medium")
    if intensity not in SCHEDULE:
        intensity = "medium"
    experience = u.get("experience", "beginner")
    cat = goal_category(goal)
    sessions = SESSIONS[cat]
    sets = SETS[intensity]
    if experience == "beginner":
        sets = max(2, sets - 1)
    elif experience == "advanced":
        sets += 1

    lines = [
        f"## 7-Day {LABEL[cat]} Plan ({intensity.title()} intensity)",
        f"A {sum(SCHEDULE[intensity])}-training-day week built around your goal of \"{goal}\". "
        f"{EXPERIENCE_NOTE.get(experience, '')}",
        "",
    ]
    session_no = 0
    for day, trains in enumerate(SCHEDULE[intensity], start=1):
        if not trains:
            lines += [
                f"## Day {day}: Rest and recovery",
                "**Warm-up (5-10 min):** None needed",
                "**Main workout:**",
                "- Easy 20-30 min walk or gentle stretching - optional",
                "**Cooldown / recovery:** Drink plenty of water and aim for 7-9 hours of sleep.",
                "",
            ]
            continue
        title, kind, exercises = sessions[session_no % len(sessions)]
        session_no += 1
        lines += [
            f"## Day {day}: {title}",
            f"**Warm-up (5-10 min):** {WARMUPS[kind]}",
            f"**Main workout** (rest {REST[intensity]} between sets):",
        ]
        lines += [f"- {name} - {presc.format(s=sets)}" for name, presc in exercises]
        lines += [f"**Cooldown / recovery:** {COOLDOWNS[kind]}", ""]

    lines += [
        "## Important Notes",
        "- Progressive overload: add a little weight, a rep or a set each week.",
        "- Form first: stop a set when your technique breaks down.",
        "- Hydration: drink water before, during and after training.",
        "- Listen to your body: sharp pain means stop. Speak to a doctor if it persists or if you have a medical condition.",
    ]
    if u.get("notes"):
        lines.append(f"- Your note: \"{u['notes']}\". Adapt any exercise that does not suit you.")
    return "\n".join(lines) + "\n"
