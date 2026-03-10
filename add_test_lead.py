from salesbud.models.lead import add_lead

lead_id = add_lead(
    linkedin_url="https://www.linkedin.com/in/marouf-shah-099224250/",
    name="Marouf Shah",
    headline="Software Engineer",
    company="Synto Labs",
    location="Remote"
)
print(f"Added Marouf Shah as lead #{lead_id}")
