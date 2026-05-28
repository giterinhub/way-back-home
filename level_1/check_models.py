from google import genai
 
client = genai.Client(
    vertexai=True,
    project="<PROJECT_ID>", #Replace with your PROJECT_ID
    location="<ZONE>",      #Replace with your ZONE
)
 
models = client.models.list()
 
for m in models:
    print(m.name)
