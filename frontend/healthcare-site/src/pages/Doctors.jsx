import React from 'react';
import { Link } from 'react-router-dom';
import './Doctors.css';

const doctors = [
  {
    name: 'Dr. Sarah Mitchell',
    specialty: 'Cardiology',
    exp: '18 years',
    desc: 'Leading cardiologist specializing in interventional cardiology and heart failure management.',
    avatar: 'SM',
    color: '#0d9488',
  },
  {
    name: 'Dr. James Wilson',
    specialty: 'Neurology',
    exp: '15 years',
    desc: 'Expert neurologist focused on stroke care, epilepsy, and neurodegenerative disorders.',
    avatar: 'JW',
    color: '#0891b2',
  },
  {
    name: 'Dr. Emily Park',
    specialty: 'Pediatrics',
    exp: '12 years',
    desc: 'Compassionate pediatrician dedicated to children\'s health from infancy through adolescence.',
    avatar: 'EP',
    color: '#7c3aed',
  },
  {
    name: 'Dr. Robert Chen',
    specialty: 'Orthopedics',
    exp: '20 years',
    desc: 'Renowned orthopedic surgeon specializing in joint replacement and sports medicine.',
    avatar: 'RC',
    color: '#ea580c',
  },
  {
    name: 'Dr. Lisa Thompson',
    specialty: 'Oncology',
    exp: '14 years',
    desc: 'Oncologist committed to personalized cancer care with cutting-edge treatment approaches.',
    avatar: 'LT',
    color: '#dc2626',
  },
  {
    name: 'Dr. Michael Rivera',
    specialty: 'Pulmonology',
    exp: '16 years',
    desc: 'Pulmonology specialist focused on respiratory diseases and sleep medicine.',
    avatar: 'MR',
    color: '#ca8a04',
  },
  {
    name: 'Dr. Anna Kowalski',
    specialty: 'Ophthalmology',
    exp: '11 years',
    desc: 'Skilled ophthalmologist providing advanced eye care and vision correction procedures.',
    avatar: 'AK',
    color: '#0891b2',
  },
  {
    name: 'Dr. David Okafor',
    specialty: 'Emergency Medicine',
    exp: '13 years',
    desc: 'Experienced emergency physician leading trauma response and critical care teams.',
    avatar: 'DO',
    color: '#0d9488',
  },
];

const specialties = [...new Set(doctors.map(d => d.specialty))];

export default function Doctors() {
  const [activeSpecialty, setActiveSpecialty] = React.useState('All');

  const filtered = activeSpecialty === 'All'
    ? doctors
    : doctors.filter(d => d.specialty === activeSpecialty);

  return (
    <>
      {/* ========== PAGE HEADER ========== */}
      <section className="page-header">
        <div className="container page-header__inner animate-in">
          <span className="section-tag">Our Team</span>
          <h1>Meet Our Expert Doctors</h1>
          <p>
            Our team of highly qualified and compassionate medical professionals is dedicated
            to providing you with the best possible care.
          </p>
        </div>
      </section>

      {/* ========== FILTER ========== */}
      <section className="doctors-filter">
        <div className="container">
          <div className="doctors-filter__tabs animate-in">
            <button
              className={`doctors-filter__tab ${activeSpecialty === 'All' ? 'active' : ''}`}
              onClick={() => setActiveSpecialty('All')}
            >
              All Doctors
            </button>
            {specialties.map(s => (
              <button
                key={s}
                className={`doctors-filter__tab ${activeSpecialty === s ? 'active' : ''}`}
                onClick={() => setActiveSpecialty(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ========== DOCTORS GRID ========== */}
      <section className="section doctors-page">
        <div className="container">
          {filtered.length > 0 ? (
            <div className="doctors__grid">
              {filtered.map((d, i) => (
                <div
                  key={i}
                  className="doctor-card animate-in"
                  style={{ animationDelay: `${0.05 + i * 0.06}s` }}
                >
                  <div className="doctor-card__avatar" style={{ background: d.color }}>
                    {d.avatar}
                  </div>
                  <h3 className="doctor-card__name">{d.name}</h3>
                  <span className="doctor-card__specialty">{d.specialty}</span>
                  <span className="doctor-card__exp">{d.exp} experience</span>
                  <p className="doctor-card__desc">{d.desc}</p>
                  <Link to="/contact" className="btn btn-primary doctor-card__btn">
                    Book Appointment
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <p className="doctors__empty">No doctors found for this specialty.</p>
          )}
        </div>
      </section>

      {/* ========== JOIN TEAM CTA ========== */}
      <section className="cta-banner">
        <div className="container">
          <div className="cta-banner__inner animate-in">
            <h2>Join Our Medical Team</h2>
            <p>We're always looking for talented medical professionals to join our growing family.</p>
            <Link to="/contact" className="btn btn-primary">
              View Careers
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
