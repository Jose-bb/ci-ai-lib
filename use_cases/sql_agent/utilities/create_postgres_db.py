import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import date

Base = declarative_base()

class Campana(Base):
    __tablename__ = 'campanas'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    presupuesto = Column(Float)
    fecha_inicio = Column(Date)

class Lead(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    email = Column(String)
    origen = Column(String)
    campana_id = Column(Integer, ForeignKey('campanas.id'))

DATABASE_URI = os.getenv(
    "POSTGRES_CRM_URI", 
    "postgresql+psycopg2://admin:admin@host.docker.internal:5432/crm_db"
)

def init_db():
    print(f"Conectando a {DATABASE_URI}...")
    engine = create_engine(DATABASE_URI)
    
    # Clean slate and create tables
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Insert marketing campaigns
    c1 = Campana(nombre='Black Friday', presupuesto=5000.0, fecha_inicio=date(2026, 11, 20))
    c2 = Campana(nombre='Campaña Verano', presupuesto=3000.0, fecha_inicio=date(2026, 6, 1))
    session.add_all([c1, c2])
    session.commit()
    
    # Insert leads
    l1 = Lead(nombre='Juan Perez', email='juan@test.com', origen='Facebook', campana_id=c1.id)
    l2 = Lead(nombre='Maria Gomez', email='maria@test.com', origen='Google', campana_id=c2.id)
    session.add_all([l1, l2])
    session.commit()
    
    print("¡Base de datos CRM (PostgreSQL) poblada con éxito!")

if __name__ == '__main__':
    init_db()