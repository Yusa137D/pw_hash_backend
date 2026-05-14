from zxcvbn import zxcvbn

def get_strength_label(password):
    results = zxcvbn(password)
    score = results['score']
    
    labels = {
        0: "Very Weak",
        1: "Weak",
        2: "Fair",
        3: "Strong",
        4: "Very Strong"
    }
    return labels.get(score, "Unknown")