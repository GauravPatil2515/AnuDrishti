import re

with open('src/index.css', 'r') as f:
    content = f.read()

replacements = [
    (r'  @apply pill text-emerald-400 border-emerald-500/30;', 
     r'  @apply pill text-emerald-400;\n  border-color: rgba(16, 185, 129, 0.3);'),
    (r'  @apply pill text-amber-400 border-amber-500/30;', 
     r'  @apply pill text-amber-400;\n  border-color: rgba(245, 158, 11, 0.3);'),
    (r'  @apply pill text-indigo-400 border-indigo-500/30;', 
     r'  @apply pill text-indigo-400;\n  border-color: rgba(94, 106, 210, 0.3);'),
    (r'  @apply pill text-violet-400 border-violet-500/30;', 
     r'  @apply pill text-violet-400;\n  border-color: rgba(139, 92, 246, 0.3);'),
    (r'  @apply pill bg-white/5 text-white/70 border-white/10;', 
     r'  @apply pill;\n  background-color: rgba(255, 255, 255, 0.05);\n  color: rgba(255, 255, 255, 0.7);\n  border-color: rgba(255, 255, 255, 0.1);'),
    (r'  @apply btn bg-transparent text-white/70;', 
     r'  @apply btn bg-transparent;\n  color: rgba(255, 255, 255, 0.7);'),
    (r'  @apply bg-white/5 backdrop-blur-xl border border-border;', 
     r'  @apply backdrop-blur-xl border border-border;\n  background-color: rgba(255, 255, 255, 0.05);')
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

with open('src/index.css', 'w') as f:
    f.write(content)

print("Fixed index.css")
