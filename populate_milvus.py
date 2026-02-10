from pymilvus import connections, Collection, utility
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.embeddings import embed_text
from src.utils.logger import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to Milvus
connections.connect(
    alias="default",
    uri=os.getenv("MILVUS_URI"),
    token=os.getenv("MILVUS_API_KEY")
)

# Career knowledge data
CAREER_DATA = [
    {
        "text": "Data Scientists analyze large datasets using statistical methods, machine learning, and programming to extract insights and help organizations make data-driven decisions. They work with Python, R, SQL, and various ML frameworks. Strong foundations in mathematics, statistics, and programming are essential. Career progression includes Senior Data Scientist, Lead Data Scientist, and Chief Data Officer roles.",
        "career_path": "Data Scientist",
        "skills": "Python, Machine Learning, Statistics, SQL, Data Visualization, R, Deep Learning, Feature Engineering, A/B Testing"
    },
    {
        "text": "Software Engineers design, develop, test, and maintain software applications and systems. They work with various programming languages, frameworks, and tools to create scalable solutions. Key skills include algorithms, data structures, system design, and software architecture. Career paths include Full Stack Developer, Backend Engineer, Frontend Engineer, DevOps Engineer, and Engineering Manager.",
        "career_path": "Software Engineer",
        "skills": "JavaScript, Python, Java, Git, Algorithms, Data Structures, REST APIs, Databases, Testing, CI/CD, Cloud Platforms"
    },
    {
        "text": "Product Managers define product vision, strategy, and roadmap. They work closely with engineering, design, marketing, and sales teams to deliver products that meet customer needs and business goals. Skills include user research, market analysis, roadmap planning, stakeholder management, and data analysis. Career progression includes Senior PM, Group PM, Director of Product, and VP of Product.",
        "career_path": "Product Manager",
        "skills": "Product Strategy, User Research, Roadmapping, Agile, Data Analysis, Communication, Stakeholder Management, Market Research, PRD Writing"
    },
    {
        "text": "UX/UI Designers create intuitive and engaging user experiences for digital products. They conduct user research, create wireframes and prototypes, and work with developers to implement designs. Tools include Figma, Sketch, Adobe XD, and prototyping tools. Skills needed are design thinking, user research, visual design, interaction design, and usability testing.",
        "career_path": "UX/UI Designer",
        "skills": "Figma, Sketch, User Research, Wireframing, Prototyping, Visual Design, Interaction Design, Usability Testing, Design Systems"
    },
    {
        "text": "DevOps Engineers bridge the gap between development and operations, focusing on automation, CI/CD, infrastructure management, and monitoring. They work with cloud platforms, containerization, and infrastructure as code. Essential skills include Linux, Docker, Kubernetes, AWS/Azure/GCP, Jenkins, and scripting languages.",
        "career_path": "DevOps Engineer",
        "skills": "Docker, Kubernetes, Jenkins, AWS, Azure, GCP, Linux, CI/CD, Terraform, Ansible, Monitoring, Scripting"
    },
    {
        "text": "Machine Learning Engineers develop and deploy ML models into production systems. They combine software engineering skills with ML expertise to build scalable ML solutions. Skills include Python, TensorFlow, PyTorch, MLOps, model deployment, and feature engineering. Roles evolve to Senior MLE, ML Architect, and Head of ML.",
        "career_path": "Machine Learning Engineer",
        "skills": "Python, TensorFlow, PyTorch, Scikit-learn, MLOps, Model Deployment, Feature Engineering, Deep Learning, NLP, Computer Vision"
    },
    {
        "text": "Digital Marketing Specialists create and execute online marketing campaigns across various channels including SEO, SEM, social media, email, and content marketing. They analyze campaign performance, optimize conversion rates, and manage marketing budgets. Key skills include Google Analytics, SEO, SEM, social media marketing, and content strategy.",
        "career_path": "Digital Marketing Specialist",
        "skills": "SEO, SEM, Google Analytics, Social Media Marketing, Content Marketing, Email Marketing, PPC, Conversion Optimization, Marketing Automation"
    },
    {
        "text": "Business Analysts bridge the gap between business needs and technical solutions. They gather requirements, analyze business processes, and recommend improvements. Skills include data analysis, process modeling, requirements documentation, SQL, and stakeholder communication. Career paths include Senior BA, Product Owner, and Business Consultant.",
        "career_path": "Business Analyst",
        "skills": "Requirements Gathering, Process Modeling, Data Analysis, SQL, Excel, Business Intelligence, Documentation, Stakeholder Management, Agile"
    },
    {
        "text": "Cybersecurity Analysts protect organizations from cyber threats by monitoring systems, identifying vulnerabilities, and implementing security measures. They need knowledge of network security, penetration testing, incident response, and security tools. Certifications like CISSP, CEH, and Security+ are valuable.",
        "career_path": "Cybersecurity Analyst",
        "skills": "Network Security, Penetration Testing, Incident Response, SIEM Tools, Firewall Configuration, Security Auditing, Risk Assessment, Encryption"
    },
    {
        "text": "Cloud Architects design and implement cloud infrastructure solutions using AWS, Azure, or GCP. They ensure scalability, security, and cost-optimization of cloud resources. Skills include cloud platforms, networking, security, infrastructure as code, and system architecture. Senior roles include Principal Cloud Architect and Cloud Solutions Director.",
        "career_path": "Cloud Architect",
        "skills": "AWS, Azure, GCP, Cloud Architecture, Networking, Security, Terraform, CloudFormation, Microservices, Serverless, Cost Optimization"
    },
    {
        "text": "Content Writers and Copywriters create compelling written content for websites, blogs, marketing materials, and social media. They need strong writing skills, creativity, SEO knowledge, and the ability to adapt tone for different audiences. Specializations include technical writing, content marketing, and creative copywriting.",
        "career_path": "Content Writer/Copywriter",
        "skills": "Writing, Editing, SEO, Content Strategy, Research, Creative Writing, Grammar, WordPress, Content Management, Social Media"
    },
    {
        "text": "Project Managers plan, execute, and close projects while managing resources, timelines, and stakeholders. They use methodologies like Agile, Scrum, or Waterfall. Key skills include planning, risk management, communication, and tools like Jira, Asana, or MS Project. Certifications like PMP and CSM are valuable.",
        "career_path": "Project Manager",
        "skills": "Project Planning, Agile, Scrum, Risk Management, Stakeholder Management, Budgeting, Communication, Jira, MS Project, Leadership"
    },
    {
        "text": "Data Engineers build and maintain data infrastructure, pipelines, and warehouses. They work with big data technologies, ETL processes, and databases to ensure data is accessible and reliable. Skills include SQL, Python, Spark, Airflow, and data modeling. Career growth includes Senior Data Engineer and Data Architect roles.",
        "career_path": "Data Engineer",
        "skills": "SQL, Python, Apache Spark, Airflow, ETL, Data Warehousing, Kafka, Hadoop, Data Modeling, Cloud Data Services, NoSQL"
    },
    {
        "text": "Mobile App Developers create applications for iOS and Android platforms. They use languages like Swift, Kotlin, Java, or cross-platform frameworks like React Native and Flutter. Skills include mobile UI/UX, API integration, app store deployment, and mobile security. Roles advance to Senior Mobile Developer and Mobile Architect.",
        "career_path": "Mobile App Developer",
        "skills": "Swift, Kotlin, Java, React Native, Flutter, Mobile UI/UX, REST APIs, Git, App Store Deployment, Firebase, Mobile Security"
    },
    {
        "text": "Financial Analysts analyze financial data to help businesses make investment decisions and strategic plans. They create financial models, forecasts, and reports. Skills include financial modeling, Excel, accounting principles, data analysis, and business intelligence tools. Career paths include Senior Analyst, Finance Manager, and CFO.",
        "career_path": "Financial Analyst",
        "skills": "Financial Modeling, Excel, Accounting, Financial Reporting, Data Analysis, Bloomberg, Forecasting, Budgeting, Investment Analysis"
    }
]


def create_collection_if_not_exists():
    """Create Milvus collection if it doesn't exist"""
    from pymilvus import FieldSchema, CollectionSchema, DataType, Collection
    
    collection_name = "career_vectors"
    
    if utility.has_collection(collection_name):
        logger.info(f"Collection '{collection_name}' already exists")
        return Collection(collection_name)
    
    logger.info(f"Creating collection '{collection_name}'")
    
    # Define schema
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="career_path", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="skills", dtype=DataType.VARCHAR, max_length=2000),
    ]
    
    schema = CollectionSchema(fields, description="Career guidance knowledge base")
    collection = Collection(name=collection_name, schema=schema)
    
    # Create index
    index_params = {
        "metric_type": "IP",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    
    logger.info(f"Collection '{collection_name}' created successfully")
    return collection


def populate_data():
    """Populate Milvus with career data"""
    try:
        # Create or get collection
        collection = create_collection_if_not_exists()
        
        logger.info(f"Populating {len(CAREER_DATA)} career entries...")
        
        embeddings = []
        texts = []
        career_paths = []
        skills_list = []
        
        for i, data in enumerate(CAREER_DATA):
            logger.info(f"Processing {i+1}/{len(CAREER_DATA)}: {data['career_path']}")
            
            # Generate embedding
            embedding = embed_text(data["text"])
            
            embeddings.append(embedding)
            texts.append(data["text"])
            career_paths.append(data["career_path"])
            skills_list.append(data["skills"])
        
        # Insert data
        logger.info("Inserting data into Milvus...")
        entities = [
            embeddings,
            texts,
            career_paths,
            skills_list
        ]
        
        insert_result = collection.insert(entities)
        collection.flush()
        
        logger.info(f"Successfully inserted {len(insert_result.primary_keys)} entries")
        logger.info("Loading collection...")
        collection.load()
        
        # Verify
        count = collection.num_entities
        logger.info(f"Total entities in collection: {count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error populating data: {str(e)}")
        return False


if __name__ == "__main__":
    logger.info("Starting Milvus population script...")
    success = populate_data()
    
    if success:
        logger.info("✓ Data population completed successfully!")
    else:
        logger.error("✗ Data population failed!")
        sys.exit(1)