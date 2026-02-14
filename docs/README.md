# Documentation Development

This directory contains the Jekyll-based documentation for **bbl-shutter-cam**, published via GitHub Pages.

## Viewing Documentation

**Live site:** https://bodybybuddha.github.io/bbl-shutter-cam/

## Testing Locally (Optional)

To preview documentation changes before pushing:

### Prerequisites
- Ruby 2.7+ and Bundler
- Install with: `sudo apt install ruby-full build-essential` (Debian/Ubuntu)

### Setup
```bash
cd docs/
bundle install
```

### Preview
```bash
bundle exec jekyll serve
# Visit: http://localhost:4000/bbl-shutter-cam/
```

Changes to markdown files will auto-reload in your browser.

### Clean Build
```bash
bundle exec jekyll clean
bundle exec jekyll serve
```

## Theme

This site uses [Just the Docs](https://just-the-docs.com/) theme with:
- Search functionality
- Responsive navigation
- Code syntax highlighting
- Dark mode support

## Structure

```
docs/
├── _config.yml           # Jekyll configuration
├── Gemfile              # Ruby dependencies
├── index.md             # Homepage
├── installation/        # Setup guides
├── user-guide/          # Usage documentation
├── features/            # Feature explanations
├── advanced/            # Advanced topics
├── faq.md              # Frequently asked questions
└── troubleshooting.md  # Common issues
```

## Editing Tips

### Front Matter
All pages need YAML front matter:

```yaml
---
layout: page
title: Page Title
nav_order: 2
parent: Installation  # Optional, for sub-pages
---
```

### Navigation Order
Control sidebar order with `nav_order` (lower numbers = higher in list).

### Code Blocks
Use triple backticks with language identifier:

````markdown
```python
print("Hello World")
```
````

### Internal Links
Use relative paths from docs root:
```markdown
[Setup Guide](installation/setup-pi.md)
```

## GitHub Pages Deployment

GitHub Pages automatically rebuilds the site when commits are pushed to the `main` branch. No manual build needed!

Check deployment status: https://github.com/bodybybuddha/bbl-shutter-cam/deployments
