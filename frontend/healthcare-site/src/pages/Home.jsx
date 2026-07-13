import React from 'react';
import { Link } from 'react-router-dom';
import { preloadPage } from '../utils/preload.js';
import './Home.css';

const features = [
  {
    icon: '🚑',
    title: '24/7 Emergency Care',
    desc: 'Round-the-clock emergency services with rapid response teams and state-of-the-art trauma care.',
  },
  {
    icon: '❤️',
    title: 'Cardiology',
    desc: 'Comprehensive heart care with advanced diagnostics, interventional procedures, and rehabilitation.',
  },
  {
    icon: '🧠',
    title: 'Neurology',
    desc: 'Expert neurological care for conditions affecting the brain, spine, and nervous system.',
  },
  {
    icon: '🦴',
    title: 'Orthopedics',
    desc: 'Complete musculoskeletal care from sports injuries to joint replacements and rehabilitation.',
  },
  {
    icon: '👶',
    title: 'Pediatrics',
    desc: 'Family-centered pediatric care covering everything from well-child visits to complex conditions.',
  },
  {
    icon: '🔬',
    title: 'Diagnostic Imaging',
    desc: 'Advanced imaging technology including MRI, CT scans, ultrasound, and digital X-ray services.',
  },
];

const stats = [
  { value: '25+', label: 'Years Experience' },
  { value: '50K+', label: 'Patients Treated' },
  { value: '200+', label: 'Expert Doctors' },
  { value: '98%', label: 'Patient Satisfaction' },
];

const testimonials = [
  {
    name: 'Sarah Johnson',
    role: 'Patient',
    text: 'The care I received at MediCare+ was exceptional. From the moment I walked in, every staff member was compassionate and professional. Truly a life-changing experience.',
    rating: 5,
  },
  {
    name: 'Michael Chen',
    role: 'Patient',
    text: 'After years of searching for the right treatment, the cardiology team at MediCare+ finally gave me my life back. I cannot recommend them enough.',
    rating: 5,
  },
  {
    name: 'Emily Rodriguez',
    role: 'Patient Family Member',
    text: 'My mother received outstanding care during her stay. The doctors kept us informed every step of the way. So grateful for this incredible team.',
    rating: 5,
  },
];

export default function Home() {
  return (
    <>
      {/* ========== HERO ========== */}
      <section className="hero">
        <div className="hero__bg-pattern" />
        <div className="container hero__inner">
          <div className="hero__content animate-in">
            <span className="section-tag">Welcome to MediCare+</span>
            <h1>Your Health Is Our <span className="hero__highlight">Greatest Priority</span></h1>
            <p>
              We provide compassionate, world-class healthcare services with cutting-edge technology
              and a team of dedicated medical professionals committed to your well-being.
            </p>
            <div className="hero__actions">
              <Link
                to="/booking"
                className="btn btn-primary"
                onMouseEnter={() => preloadPage('/booking')}
              >
                Book an Appointment
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </Link>
              <Link
                to="/services"
                className="btn btn-secondary"
                onMouseEnter={() => preloadPage('/services')}
              >
                Our Services
              </Link>
            </div>
            <div className="hero__trust">
              <div className="hero__avatars">
                <span>😊</span><span>👨‍⚕️</span><span>👩‍⚕️</span><span>👍</span>
              </div>
              <p>Trusted by <strong>50,000+</strong> patients</p>
            </div>
          </div>
          <div className="hero__visual animate-in animate-in-delay-2">
            <div className="hero__image-wrapper">
              <div className="hero__image-placeholder">
                <div className="hero__image-icon">🏥</div>
                <div className="hero__image-decoration" />
              </div>
              <div className="hero__badge hero__badge--1">
                <span>👨‍⚕️</span>
                <div>
                  <strong>200+</strong>
                  <small>Expert Doctors</small>
                </div>
              </div>
              <div className="hero__badge hero__badge--2">
                <span>⭐</span>
                <div>
                  <strong>4.9</strong>
                  <small>Patient Rating</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========== FEATURES ========== */}
      <section className="section features">
        <div className="container">
          <div className="section-header animate-in">
            <span className="section-tag">Our Services</span>
            <h2>Comprehensive Medical Care Under One Roof</h2>
            <p>From emergency services to specialized treatments, we offer a full spectrum of healthcare services tailored to your needs.</p>
          </div>
          <div className="features__grid">
            {features.map((f, i) => (
              <div
                key={i}
                className="feature-card animate-in"
                style={{ animationDelay: `${0.1 + i * 0.08}s` }}
              >
                <div className="feature-card__icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
            <Link
              to="/services"
              className="feature-card__link"
              onMouseEnter={() => preloadPage('/services')}
            >
              Learn more
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== STATS ========== */}
      <section className="stats-section">
        <div className="container">
          <div className="stats__grid">
            {stats.map((s, i) => (
              <div key={i} className="stat-item animate-in" style={{ animationDelay: `${0.1 + i * 0.1}s` }}>
                <span className="stat-value">{s.value}</span>
                <span className="stat-label">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== TESTIMONIALS ========== */}
      <section className="section testimonials">
        <div className="container">
          <div className="section-header animate-in">
            <span className="section-tag">Testimonials</span>
            <h2>What Our Patients Say</h2>
            <p>Hear from the people we've had the privilege to care for.</p>
          </div>
          <div className="testimonials__grid">
            {testimonials.map((t, i) => (
              <div
                key={i}
                className="testimonial-card animate-in"
                style={{ animationDelay: `${0.1 + i * 0.12}s` }}
              >
                <div className="testimonial-card__stars">
                  {'★'.repeat(t.rating)}{'☆'.repeat(5 - t.rating)}
                </div>
                <p className="testimonial-card__text">"{t.text}"</p>
                <div className="testimonial-card__author">
                  <div className="testimonial-card__avatar">
                    {t.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <strong>{t.name}</strong>
                    <small>{t.role}</small>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== CTA BANNER ========== */}
      <section className="cta-banner">
        <div className="container">
          <div className="cta-banner__inner animate-in">
            <h2>Ready to Prioritize Your Health?</h2>
            <p>Schedule an appointment today and take the first step towards better health.</p>
            <Link
              to="/booking"
              className="btn btn-primary"
              onMouseEnter={() => preloadPage('/booking')}
            >
              Book Your Visit
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
