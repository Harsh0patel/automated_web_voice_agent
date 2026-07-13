import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Blog.css';

const posts = [
  {
    category: 'Wellness',
    date: 'June 15, 2026',
    title: '10 Simple Habits for a Healthier Heart',
    excerpt: 'Discover daily habits that can significantly improve your cardiovascular health and reduce the risk of heart disease.',
    author: 'Dr. Sarah Mitchell',
    readTime: '5 min read',
    emoji: '❤️',
    color: '#0d9488',
  },
  {
    category: 'Nutrition',
    date: 'June 10, 2026',
    title: 'The Essential Guide to a Balanced Diet',
    excerpt: 'Learn how to build a nutritious meal plan that supports your overall health and wellness goals.',
    author: 'Dr. Lisa Thompson',
    readTime: '7 min read',
    emoji: '🥗',
    color: '#7c3aed',
  },
  {
    category: 'Mental Health',
    date: 'June 5, 2026',
    title: 'Managing Stress: Techniques That Actually Work',
    excerpt: 'Evidence-based strategies to manage stress and improve your mental well-being in daily life.',
    author: 'Dr. James Wilson',
    readTime: '6 min read',
    emoji: '🧘',
    color: '#0891b2',
  },
  {
    category: 'Pediatrics',
    date: 'May 28, 2026',
    title: 'Vaccination Schedule: What Every Parent Should Know',
    excerpt: 'A comprehensive overview of recommended vaccinations for children from infancy through adolescence.',
    author: 'Dr. Emily Park',
    readTime: '8 min read',
    emoji: '💉',
    color: '#ea580c',
  },
  {
    category: 'Wellness',
    date: 'May 20, 2026',
    title: 'The Importance of Regular Health Screenings',
    excerpt: 'Why preventive health screenings are crucial for early detection and better health outcomes.',
    author: 'Dr. Robert Chen',
    readTime: '4 min read',
    emoji: '🔬',
    color: '#ca8a04',
  },
  {
    category: 'Nutrition',
    date: 'May 12, 2026',
    title: 'Superfoods That Boost Your Immune System',
    excerpt: 'Incorporate these nutrient-rich foods into your diet to strengthen your body\'s natural defenses.',
    author: 'Dr. Anna Kowalski',
    readTime: '6 min read',
    emoji: '🍊',
    color: '#dc2626',
  },
  {
    category: 'Mental Health',
    date: 'May 5, 2026',
    title: 'Sleep Hygiene: How to Get Better Rest Tonight',
    excerpt: 'Practical tips for improving your sleep quality and establishing a healthy bedtime routine.',
    author: 'Dr. Michael Rivera',
    readTime: '5 min read',
    emoji: '😴',
    color: '#0d9488',
  },
  {
    category: 'Wellness',
    date: 'April 28, 2026',
    title: 'Exercise for Every Age: Staying Active Through Life',
    excerpt: 'Age-appropriate exercise recommendations to maintain fitness and mobility at every stage of life.',
    author: 'Dr. David Okafor',
    readTime: '7 min read',
    emoji: '🏃',
    color: '#0891b2',
  },
  {
    category: 'Pediatrics',
    date: 'April 18, 2026',
    title: 'Recognizing Early Signs of Developmental Delays',
    excerpt: 'Key developmental milestones to watch for and when to seek professional guidance for your child.',
    author: 'Dr. Emily Park',
    readTime: '9 min read',
    emoji: '👶',
    color: '#7c3aed',
  },
];

const categories = ['All', ...new Set(posts.map(p => p.category))];

export default function Blog() {
  const [activeCategory, setActiveCategory] = useState('All');

  const filtered = activeCategory === 'All'
    ? posts
    : posts.filter(p => p.category === activeCategory);

  return (
    <>
      {/* ========== PAGE HEADER ========== */}
      <section className="page-header">
        <div className="container page-header__inner animate-in">
          <span className="section-tag">Blog</span>
          <h1>Health & Wellness Blog</h1>
          <p>
            Expert insights, health tips, and the latest medical advice from our team of healthcare professionals.
          </p>
        </div>
      </section>

      {/* ========== CATEGORY FILTER ========== */}
      <section className="blog-filter">
        <div className="container">
          <div className="blog-filter__tabs animate-in">
            {categories.map(cat => (
              <button
                key={cat}
                className={`blog-filter__tab ${activeCategory === cat ? 'active' : ''}`}
                onClick={() => setActiveCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ========== ARTICLES ========== */}
      <section className="section blog-page">
        <div className="container">
          {filtered.length > 0 ? (
            <div className="blog__grid">
              {filtered.map((post, i) => (
                <article
                  key={i}
                  className="blog-card animate-in"
                  style={{ animationDelay: `${0.05 + i * 0.06}s` }}
                >
                  <div className="blog-card__visual" style={{ background: `linear-gradient(135deg, ${post.color}15, ${post.color}05)` }}>
                    <span className="blog-card__emoji">{post.emoji}</span>
                    <span className="blog-card__category">{post.category}</span>
                  </div>
                  <div className="blog-card__body">
                    <div className="blog-card__meta">
                      <span>{post.date}</span>
                      <span>•</span>
                      <span>{post.readTime}</span>
                    </div>
                    <h3 className="blog-card__title">{post.title}</h3>
                    <p className="blog-card__excerpt">{post.excerpt}</p>
                    <div className="blog-card__footer">
                      <div className="blog-card__author">
                        <div className="blog-card__avatar" style={{ background: post.color }}>
                          {post.author.split(' ').slice(1).map(n => n[0]).join('')}
                        </div>
                        <span>{post.author}</span>
                      </div>
                      <Link to="/contact" className="blog-card__read-more">
                        Read More
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M5 12h14M12 5l7 7-7 7"/>
                        </svg>
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="blog__empty">No articles found in this category.</p>
          )}
        </div>
      </section>

      {/* ========== NEWSLETTER CTA ========== */}
      <section className="cta-banner">
        <div className="container">
          <div className="cta-banner__inner animate-in">
            <h2>Stay Informed</h2>
            <p>Subscribe to our newsletter for the latest health tips, news, and updates from MediCare+.</p>
            <Link to="/contact" className="btn btn-primary">
              Subscribe Now
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
