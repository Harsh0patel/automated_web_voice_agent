import React, { useState } from 'react';
import './Contact.css';

export default function Contact() {
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    department: '',
    message: '',
  });

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Simulate form submission
    console.log('Form submitted:', formData);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <>
        <section className="page-header">
          <div className="container page-header__inner animate-in">
            <span className="section-tag">Contact Us</span>
            <h1>Get In Touch</h1>
            <p>We're here to help with any questions or concerns you may have.</p>
          </div>
        </section>
        <section className="section contact-page">
          <div className="container">
            <div className="contact__success animate-in">
              <div className="contact__success-icon">✅</div>
              <h3>Thank You! 🎉</h3>
              <p>Your message has been sent successfully. Our team will get back to you within 24 hours.</p>
              <button className="btn btn-primary" onClick={() => { setSubmitted(false); setFormData({ name: '', email: '', phone: '', department: '', message: '' }); }}>
                Send Another Message
              </button>
            </div>
          </div>
        </section>
      </>
    );
  }

  return (
    <>
      {/* ========== PAGE HEADER ========== */}
      <section className="page-header">
        <div className="container page-header__inner animate-in">
          <span className="section-tag">Contact Us</span>
          <h1>Get In Touch</h1>
          <p>
            Have a question, need to schedule an appointment, or want to learn more about our services?
            We'd love to hear from you.
          </p>
        </div>
      </section>

      {/* ========== CONTACT SECTION ========== */}
      <section className="section contact-page">
        <div className="container">
          <div className="contact__grid">
            {/* Info Cards */}
            <div className="contact__info animate-in">
              <div className="contact-info-card">
                <div className="contact-info-card__icon">📍</div>
                <div>
                  <h4>Visit Us</h4>
                  <p>123 Health Avenue, Medical District, New York, NY 10001</p>
                </div>
              </div>
              <div className="contact-info-card">
                <div className="contact-info-card__icon">📞</div>
                <div>
                  <h4>Call Us</h4>
                  <a href="tel:+15551234567">+1 (555) 123-4567</a>
                  <a href="tel:+15559876543">+1 (555) 987-6543</a>
                </div>
              </div>
              <div className="contact-info-card">
                <div className="contact-info-card__icon">✉️</div>
                <div>
                  <h4>Email Us</h4>
                  <a href="mailto:info@medicareplus.com">info@medicareplus.com</a>
                  <a href="mailto:appointments@medicareplus.com">appointments@medicareplus.com</a>
                </div>
              </div>
              <div className="contact-info-card">
                <div className="contact-info-card__icon">🕐</div>
                <div>
                  <h4>Working Hours</h4>
                  <p>Mon - Fri: 8:00 AM - 8:00 PM</p>
                  <p>Saturday: 9:00 AM - 5:00 PM</p>
                  <p>Sunday: 10:00 AM - 2:00 PM (Emergency Only)</p>
                </div>
              </div>
            </div>

            {/* Form */}
            <div className="contact__form-wrapper animate-in animate-in-delay-2">
              <h3>Send Us a Message</h3>
              <form onSubmit={handleSubmit}>
                <div className="form__row">
                  <div className="form__group">
                    <label htmlFor="name">Full Name <span>*</span></label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      placeholder="John Doe"
                      required
                    />
                  </div>
                  <div className="form__group">
                    <label htmlFor="email">Email <span>*</span></label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="john@example.com"
                      required
                    />
                  </div>
                </div>
                <div className="form__row">
                  <div className="form__group">
                    <label htmlFor="phone">Phone Number</label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>
                  <div className="form__group">
                    <label htmlFor="department">Department</label>
                    <select
                      id="department"
                      name="department"
                      value={formData.department}
                      onChange={handleChange}
                    >
                      <option value="">Select a department</option>
                      <option value="cardiology">Cardiology</option>
                      <option value="neurology">Neurology</option>
                      <option value="pediatrics">Pediatrics</option>
                      <option value="orthopedics">Orthopedics</option>
                      <option value="oncology">Oncology</option>
                      <option value="general">General Medicine</option>
                      <option value="billing">Billing & Insurance</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>
                <div className="form__group full-width">
                  <label htmlFor="message">Message <span>*</span></label>
                  <textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    placeholder="How can we help you?"
                    required
                  />
                </div>
                <button type="submit" className="btn btn-primary form__submit">
                  Send Message
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                  </svg>
                </button>
              </form>
            </div>
          </div>

          {/* Map placeholder */}
          <div className="contact__map animate-in">
            <span>🗺️</span>
            <p>Interactive Map — 123 Health Avenue, New York</p>
          </div>
        </div>
      </section>
    </>
  );
}
