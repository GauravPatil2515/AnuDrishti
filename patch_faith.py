import re

with open("backend/models/faithfulness_validator.py", "r") as f:
    content = f.read()

new_content = content.replace("_, predictions, _ = self.model(data, return_attention=False)",
                              "_, predictions = self.model(data, return_attention=False)")

with open("backend/models/faithfulness_validator.py", "w") as f:
    f.write(new_content)

print("Patched faithfulness validator")
