import React from 'react';
import { Link } from 'react-router-dom';
import './Services.css';

const services = [
  {
    icon: '🚑',
    title: 'Emergency Care',
    desc: '24/7 emergency medical services with rapid response teams, advanced life support, and trauma care facilities.',
    features: ['Immediate Triage', 'Trauma Care', 'Ambulance Services', 'Critical Care Unit'],
  },
  {
    icon: '❤️',
    title: 'Cardiology',
    desc: 'Comprehensive heart care including diagnostics, interventional cardiology, and cardiac rehabilitation programs.',
    features: ['Echocardiography', 'Angioplasty', 'Heart Surgery', 'Cardiac Rehab'],
  },
  {
    icon: '🧠',
    title: 'Neurology',
    desc: 'Expert diagnosis and treatment of disorders affecting the brain, spinal cord, and nervous system.',
    features: ['Brain Imaging', 'Stroke Care', 'Epilepsy Treatment', 'Neuro Surgery'],
  },
  {
    icon: '🦴',
    title: 'Orthopedics',
    desc: 'Complete care for musculoskeletal conditions, from sports injuries to joint replacements.',
    features: ['Joint Replacement', 'Sports Medicine', 'Spine Surgery', 'Physical Therapy'],
  },
  {
    icon: '👶',
    title: 'Pediatrics',
    desc: 'Family-centered healthcare for infants, children, and adolescents in a welcoming environment.',
    features: ['Well-child Visits', 'Vaccinations', 'Developmental Screenings', 'Pediatric ICU'],
  },
  {
    icon: '🔬',
    title: 'Diagnostic Imaging',
    desc: 'State-of-the-art imaging technology for accurate diagnosis and treatment planning.',
    features: ['MRI & CT Scans', 'Ultrasound', 'X-Ray', 'PET Scans'],
  },
  {
    icon: '🫁',
    title: 'Pulmonology',
    desc: 'Specialized care for respiratory conditions affecting the lungs and breathing.',
    features: ['Pulmonary Function', 'Bronchoscopy', 'Sleep Studies', 'Asthma Management'],
  },
  {
    icon: '🧬',
    title: 'Oncology',
    desc: 'Comprehensive cancer care with advanced treatment options and supportive services.',
    features: ['Chemotherapy', 'Radiation Therapy', 'Immunotherapy', 'Cancer Screening'],
  },
  {
    icon: '👁️',
    title: 'Ophthalmology',
    desc: 'Complete eye care services from routine exams to advanced surgical procedures.',
    features: ['Cataract Surgery', 'Glaucoma Care', 'LASIK', 'Retina Treatment'],
  },
];

export default function Services() {
  return (
    <>
      {/* ========== PAGE HEADER ========== */}
      <section className="page-header">
        <div className="container page-header__inner animate-in">
          <span className="section-tag">Our Services</span>
          <h1>World-Class Medical Services</h1>
          <p>
            From routine check-ups to specialized treatments, we offer a comprehensive range
            of healthcare services delivered with compassion and expertise.
          </p>
        </div>
      </section>

      {/* ========== SERVICES GRID ========== */}
      <section className="section services-page">
        <div className="container">
          <div className="services-page__grid">
            {services.map((s, i) => (
              <div
                key={i}
                className="service-card animate-in"
                style={{ animationDelay: `${0.05 + i * 0.06}s` }}
              >
                <div className="service-card__header">
                  <span className="service-card__icon">{s.icon}</span>
                  <h3>{s.title}</h3>
                </div>
                <p className="service-card__desc">{s.desc}</p>
                <ul className="service-card__features">
                  {s.features.map((f, j) => (
                    <li key={j}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d9488" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== WHY CHOOSE US ========== */}
      <section className="section why-choose">
        <div className="container">
          <div className="section-header animate-in">
            <span className="section-tag">Why Choose Us</span>
            <h2>What Sets Us Apart</h2>
          </div>
          <div className="why-choose__grid">
            {[
              { icon: '👨‍⚕️', title: 'Expert Specialists', desc: 'Board-certified physicians with years of specialized training and experience.' },
              { icon: '💡', title: 'Cutting-Edge Technology', desc: 'Latest medical equipment and techniques for accurate diagnosis and treatment.' },
              { icon: '🤝', title: 'Patient-Centered Care', desc: 'Personalized treatment plans tailored to your unique health needs.' },
            ].map((item, i) => (
              <div key={i} className="why-choose__card animate-in" style={{ animationDelay: `${0.1 + i * 0.1}s` }}>
                <span className="why-choose__icon">{item.icon}</span>
                <h4>{item.title}</h4>
                <p>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== CTA ========== */}
      <section className="cta-banner">
        <div className="container">
          <div className="cta-banner__inner animate-in">
            <h2>Need a Specialist?</h2>
            <p>Our team of experts is ready to help you. Schedule a consultation today.</p>
            <Link to="/contact" className="btn btn-primary">
              Book Appointment
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
