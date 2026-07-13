import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Careers.css';

const jobs = [
  {
    title: 'Registered Nurse (RN)',
    department: 'Nursing',
    location: 'New York, NY',
    type: 'Full-Time',
    desc: 'Provide direct patient care, administer medications, and collaborate with physicians to deliver exceptional healthcare outcomes.',
    color: '#0d9488',
  },
  {
    title: 'Physician Assistant',
    department: 'Medical',
    location: 'New York, NY',
    type: 'Full-Time',
    desc: 'Diagnose and treat patients under physician supervision, perform procedures, and manage treatment plans.',
    color: '#0891b2',
  },
  {
    title: 'Medical Laboratory Technician',
    department: 'Diagnostics',
    location: 'New York, NY',
    type: 'Full-Time',
    desc: 'Perform laboratory tests, analyze specimens, and ensure accurate diagnostic results for patient care.',
    color: '#7c3aed',
  },
  {
    title: 'Patient Care Coordinator',
    department: 'Administration',
    location: 'New York, NY',
    type: 'Full-Time',
    desc: 'Coordinate patient appointments, manage schedules, and serve as a liaison between patients and medical staff.',
    color: '#ea580c',
  },
  {
    title: 'Physical Therapist',
    department: 'Rehabilitation',
    location: 'New York, NY',
    type: 'Part-Time',
    desc: 'Develop and implement rehabilitation programs to help patients recover mobility and manage pain.',
    color: '#ca8a04',
  },
  {
    title: 'IT Support Specialist',
    department: 'Technology',
    location: 'Remote',
    type: 'Full-Time',
    desc: 'Provide technical support, maintain healthcare systems, and ensure data security compliance.',
    color: '#dc2626',
  },
  {
    title: 'Medical Biller / Coder',
    department: 'Billing',
    location: 'New York, NY',
    type: 'Full-Time',
    desc: 'Process medical claims, verify insurance coverage, and ensure accurate coding for reimbursements.',
    color: '#0d9488',
  },
  {
    title: 'Pharmacy Technician',
    department: 'Pharmacy',
    location: 'New York, NY',
    type: 'Part-Time',
    desc: 'Assist pharmacists in preparing medications, managing inventory, and serving patients.',
    color: '#0891b2',
  },
];

const departments = ['All', ...new Set(jobs.map(j => j.department))];

const benefits = [
  { icon: '🏥', title: 'Health Insurance', desc: 'Comprehensive medical, dental, and vision coverage for you and your family.' },
  { icon: '💰', title: 'Competitive Salary', desc: 'Top-tier compensation packages with performance bonuses and annual reviews.' },
  { icon: '🏖️', title: 'Paid Time Off', desc: 'Generous vacation, sick leave, and paid holidays to support work-life balance.' },
  { icon: '📚', title: 'Education Support', desc: 'Tuition reimbursement and continuous learning opportunities for career growth.' },
  { icon: '🧘', title: 'Wellness Programs', desc: 'Gym memberships, mental health support, and wellness initiative programs.' },
  { icon: '👶', title: 'Family Benefits', desc: 'Parental leave, childcare assistance, and family-friendly policies.' },
  { icon: '📈', title: 'Retirement Plans', desc: '401(k) matching and retirement planning services for your financial future.' },
  { icon: '🏆', title: 'Recognition Programs', desc: 'Employee of the month awards, team celebrations, and career advancement pathways.' },
];

export default function Careers() {
  const [activeDept, setActiveDept] = useState('All');

  const filtered = activeDept === 'All'
    ? jobs
    : jobs.filter(j => j.department === activeDept);

  return (
    <>
      {/* ========== PAGE HEADER ========== */}
      <section className="page-header">
        <div className="container page-header__inner animate-in">
          <span className="section-tag">Careers</span>
          <h1>Join Our Team</h1>
          <p>
            At MediCare+, we're building a community of passionate healthcare professionals
            dedicated to making a difference. Find your place with us.
          </p>
        </div>
      </section>

      {/* ========== CULTURE ========== */}
      <section className="section culture">
        <div className="container">
          <div className="culture__grid">
            <div className="culture__content animate-in">
              <span className="section-tag">Our Culture</span>
              <h2>More Than a Workplace</h2>
              <p>
                We believe that exceptional patient care starts with taking care of our team.
                At MediCare+, you'll find a supportive, collaborative environment where your
                contributions are valued and your growth is prioritized.
              </p>
              <div className="culture__stats">
                <div className="culture__stat">
                  <strong>500+</strong>
                  <span>Employees</span>
                </div>
                <div className="culture__stat">
                  <strong>4.8★</strong>
                  <span>Employee Rating</span>
                </div>
                <div className="culture__stat">
                  <strong>92%</strong>
                  <span>Retention Rate</span>
                </div>
              </div>
            </div>
            <div className="culture__visual animate-in animate-in-delay-2">
              <div className="culture__placeholder">
                🤝
                <p>Great People, Great Care</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========== BENEFITS ========== */}
      <section className="section benefits-section">
        <div className="container">
          <div className="section-header animate-in">
            <span className="section-tag">Benefits</span>
            <h2>What We Offer</h2>
            <p>We provide a comprehensive benefits package designed to support your well-being and professional growth.</p>
          </div>
          <div className="benefits__grid">
            {benefits.map((b, i) => (
              <div key={i} className="benefit-card animate-in" style={{ animationDelay: `${0.05 + i * 0.06}s` }}>
                <span className="benefit-card__icon">{b.icon}</span>
                <h4>{b.title}</h4>
                <p>{b.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========== OPEN POSITIONS ========== */}
      <section className="section jobs-section">
        <div className="container">
          <div className="section-header animate-in">
            <span className="section-tag">Open Positions</span>
            <h2>Current Openings</h2>
            <p>Explore our current job openings and find the role that's right for you.</p>
          </div>

          <div className="jobs-filter animate-in">
            {departments.map(dept => (
              <button
                key={dept}
                className={`jobs-filter__tab ${activeDept === dept ? 'active' : ''}`}
                onClick={() => setActiveDept(dept)}
              >
                {dept}
              </button>
            ))}
          </div>

          <div className="jobs__list">
            {filtered.length > 0 ? (
              filtered.map((job, i) => (
                <div key={i} className="job-card animate-in" style={{ animationDelay: `${0.05 + i * 0.06}s` }}>
                  <div className="job-card__left">
                    <div className="job-card__icon" style={{ background: `${job.color}15`, color: job.color }}>
                      {job.title.split(' ').map(w => w[0]).slice(0, 2).join('')}
                    </div>
                    <div>
                      <h3 className="job-card__title">{job.title}</h3>
                      <div className="job-card__tags">
                        <span className="job-card__tag job-card__tag--dept">{job.department}</span>
                        <span className="job-card__tag job-card__tag--location">{job.location}</span>
                        <span className="job-card__tag job-card__tag--type">{job.type}</span>
                      </div>
                    </div>
                  </div>
                  <div className="job-card__right">
                    <p className="job-card__desc">{job.desc}</p>
                    <Link to="/contact" className="btn btn-primary" style={{ padding: '10px 22px', fontSize: '0.8125rem' }}>
                      Apply Now
                    </Link>
                  </div>
                </div>
              ))
            ) : (
              <p className="jobs__empty">No open positions in this department right now.</p>
            )}
          </div>
        </div>
      </section>

      {/* ========== CTA ========== */}
      <section className="cta-banner">
        <div className="container">
          <div className="cta-banner__inner animate-in">
            <h2>Don't See the Right Role?</h2>
            <p>We're always looking for talented individuals. Send us your resume and we'll keep you in mind for future openings.</p>
            <Link to="/contact" className="btn btn-primary">
              Submit Your Resume
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
