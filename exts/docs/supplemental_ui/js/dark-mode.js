/**
 * Geo-Sub OptiX Dark Mode Toggle
 * Persists user preference via localStorage
 */
;(function () {
  'use strict'

  const STORAGE_KEY = 'geo-sub-dark-mode'
  const DARK_CLASS = 'dark-mode'

  function isDarkModePreferred() {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored !== null) {
      return stored === 'true'
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  }

  function setDarkMode(enabled) {
    document.documentElement.classList.toggle(DARK_CLASS, enabled)
    localStorage.setItem(STORAGE_KEY, enabled)
    updateToggleButton(enabled)
  }

  function updateToggleButton(isDark) {
    const btn = document.querySelector('.dark-mode-toggle')
    if (btn) {
      btn.textContent = isDark ? '☀️' : '🌙'
      btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode')
      btn.setAttribute('title', isDark ? 'Switch to light mode' : 'Switch to dark mode')
    }
  }

  function createToggleButton() {
    const btn = document.createElement('button')
    btn.className = 'dark-mode-toggle'
    btn.type = 'button'
    btn.addEventListener('click', function () {
      const isDark = document.documentElement.classList.contains(DARK_CLASS)
      setDarkMode(!isDark)
    })
    return btn
  }

  function injectToggle() {
    // Try navbar first, then toolbar
    const navbar = document.querySelector('.navbar-end') || 
                   document.querySelector('.navbar-item:last-child') ||
                   document.querySelector('.toolbar .tools')
    
    if (navbar) {
      const btn = createToggleButton()
      navbar.appendChild(btn)
      updateToggleButton(document.documentElement.classList.contains(DARK_CLASS))
    }
  }

  // Apply saved preference immediately (before DOM ready) to prevent flash
  if (isDarkModePreferred()) {
    document.documentElement.classList.add(DARK_CLASS)
  }

  // Inject toggle button when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectToggle)
  } else {
    injectToggle()
  }

  // Listen for system preference changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
    if (localStorage.getItem(STORAGE_KEY) === null) {
      setDarkMode(e.matches)
    }
  })
})()
