import React, { useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import useScrapedComponents from '../hooks/useScrapedComponents.js';
import './Doctors.css';

// ── Fallback data ──
const FALLBACK_DOCTORS = [
  { name: 'Dr. Sarah Mitchell', specialty: 'Cardiology', exp: '18 years', desc: 'Leading cardiologist.', avatar: 'SM', color: '#0d9488' },
  { name: 'Dr. James Wilson', specialty: 'Neurology', exp: '15 years', desc: 'Expert neurologist.', avatar: 'JW', color: '#0891b2' },
  { name: 'Dr. Emily Park', specialty: 'Pediatrics', exp: '12 years', desc: 'Compassionate pediatrician.', avatar: 'EP', color: '#7c3aed' },
  { name: 'Dr. Robert Chen', specialty: 'Orthopedics', exp: '20 years', desc: 'Renowned orthopedic surgeon.', avatar: 'RC', color: '#ea580c' },
  { name: 'Dr. Lisa Thompson', specialty: 'Oncology', exp: '14 years', desc: 'Oncologist.', avatar: 'LT', color: '#dc2626' },
  { name: 'Dr. Michael Rivera', specialty: 'Pulmonology', exp: '16 years', desc: 'Pulmonology specialist.', avatar: 'MR', color: '#ca8a04' },
  { name: 'Dr. Anna Kowalski', specialty: 'Ophthalmology', exp: '11 years', desc: 'Skilled ophthalmologist.', avatar: 'AK', color: '#0891b2' },
  { name: 'Dr. David Okafor', specialty: 'Emergency Medicine', exp: '13 years', desc: 'Experienced emergency physician.', avatar: 'DO', color: '#0d9488' },
];

const AVATAR_COLORS = ['#0d9488', '#0891b2', '#7c3aed', '#ea580c', '#dc2626', '#ca8a04'];

export default function Doctors() {
  const { byType } = useScrapedComponents();

  // Build doctors from scraped 'doctor' components, fallback to hardcoded
  const scrapedDocs = byType('doctor');
  const doctors = scrapedDocs.length > 0
    ? scrapedDocs.map(d => ({
        name: d.content,
        specialty: d.metadata?.specialty || 'General',
        exp: d.metadata?.experience || '',
        desc: d.metadata?.description || '',
        avatar: d.content.split(' ').map(n => n[0]).join('').slice(0, 2),
        color: AVATAR_COLORS[d.content.length % AVATAR_COLORS.length],
      }))
    : FALLBACK_DOCTORS;

  const specialties = [...new Set(doctors.map(d => d.specialty))];
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeSpecialty, setActiveSpecialty] = React.useState(() => {
    const fromUrl = searchParams.get('specialty');
    return fromUrl && specialties.includes(fromUrl) ? fromUrl : 'All';
  });

  // Sync URL → filter state whenever search params change
  // (handles both initial load AND subsequent navigations from the AI)
  useEffect(() => {
    const fromUrl = searchParams.get('specialty');
    if (fromUrl && specialties.includes(fromUrl)) {
      setActiveSpecialty(fromUrl);
    }
    // No else — if URL has no specialty, keep current user selection
  }, [searchParams]);

  // Sync filter state → URL when user clicks a tab
  function handleSpecialtyChange(specialty) {
    setActiveSpecialty(specialty);
    if (specialty === 'All') {
      setSearchParams({});
    } else {
      setSearchParams({ specialty });
    }
  }

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
              onClick={() => handleSpecialtyChange('All')}
            >
              All Doctors
            </button>
            {specialties.map(s => (
              <button
                key={s}
                className={`doctors-filter__tab ${activeSpecialty === s ? 'active' : ''}`}
                onClick={() => handleSpecialtyChange(s)}
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
