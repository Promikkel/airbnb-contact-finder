"""
Airbnb Contact Finder - Simplified Flask Web Application

This is a simplified version of the Airbnb Contact Finder that combines all functionality
into a single file for easier deployment and testing.
"""

import os
import re
import time
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['REPORTS_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

# Create reports directory if it doesn't exist
if not os.path.exists(app.config['REPORTS_DIR']):
    os.makedirs(app.config['REPORTS_DIR'])

# Store recent searches for demo purposes (in a production app, this would use a database)
recent_searches = []

#
# Search Functions
#

def clean_query(query):
    """
    Clean and prepare a search query by removing special characters and formatting.
    
    Args:
        query (str): The raw search query (property name, URL, or location + host)
        
    Returns:
        str: Cleaned search query
    """
    # Remove URL components if a URL was provided
    if "airbnb.com" in query.lower():
        # Extract property name from URL if possible
        parts = query.split("/")
        for i, part in enumerate(parts):
            if "rooms" in part and i+1 < len(parts):
                query = parts[i+1].replace("-", " ")
                break
        else:
            # If we couldn't extract a name, just use the URL as is
            pass
    
    # Clean the query
    query = re.sub(r'[^\w\s]', ' ', query)  # Replace special chars with spaces
    query = re.sub(r'\s+', ' ', query).strip()  # Normalize whitespace
    
    return query


def is_valid_email(email):
    """
    Check if a string is a valid email address.
    
    Args:
        email (str): String to check
        
    Returns:
        bool: True if valid email, False otherwise
    """
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email))


def extract_emails_from_text(text):
    """
    Extract email addresses from text content.
    
    Args:
        text (str): Text content to search for emails
        
    Returns:
        list: List of found email addresses
    """
    # Pattern to match email addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    # Find all matches
    emails = re.findall(email_pattern, text)
    
    # Filter out invalid matches and duplicates
    valid_emails = []
    seen = set()
    
    for email in emails:
        if email.lower() not in seen and is_valid_email(email):
            valid_emails.append(email)
            seen.add(email.lower())
    
    return valid_emails


def is_social_media_link(url, platform):
    """
    Check if a URL is a link to a specific social media platform.
    
    Args:
        url (str): URL to check
        platform (str): Social media platform (e.g., "instagram", "facebook")
        
    Returns:
        bool: True if URL is for the specified platform, False otherwise
    """
    platform_domains = {
        "instagram": ["instagram.com", "www.instagram.com"],
        "facebook": ["facebook.com", "www.facebook.com", "fb.com", "www.fb.com"],
        "twitter": ["twitter.com", "www.twitter.com", "x.com", "www.x.com"],
        "linkedin": ["linkedin.com", "www.linkedin.com"]
    }
    
    if platform.lower() not in platform_domains:
        return False
    
    try:
        parsed_url = url.lower()
        for domain in platform_domains[platform.lower()]:
            if domain in parsed_url:
                return True
        return False
    except:
        return False


#
# Contact Finder Logic
#

class ContactFinder:
    """
    Main class for finding contact information for vacation rental owners.
    """
    
    def __init__(self):
        """Initialize the ContactFinder."""
        self.results = {
            "property_info": "",
            "official_website": None,
            "email_addresses": [],
            "social_media": [],
            "contact_form": None,
            "sources": [],
            "ethical_report": []
        }
    
    def reset(self):
        """Reset the results for a new search."""
        self.results = {
            "property_info": "",
            "official_website": None,
            "email_addresses": [],
            "social_media": [],
            "contact_form": None,
            "sources": [],
            "ethical_report": []
        }
    
    def _generate_ethical_report(self):
        """Generate an ethical report for the contact information found."""
        # Start with general ethical guidelines
        self.results["ethical_report"] = [
            "Alle contactgegevens zijn verzameld uit uitsluitend openbare bronnen.",
            "Er is geen informatie verzameld van Airbnb.com of door scraping.",
            "Alle verzamelde informatie is vrijwillig door de eigenaar online gedeeld."
        ]
        
        # Add specific notes based on found information
        if self.results["official_website"]:
            self.results["ethical_report"].append(
                f"Officiële website ({self.results['official_website']}) is gevonden via openbare zoekopdracht."
            )
        
        if self.results["email_addresses"]:
            self.results["ethical_report"].append(
                f"E-mailadressen waren openbaar zichtbaar op websites beheerd door de eigenaar."
            )
        
        if self.results["social_media"]:
            platforms = [sm["platform"] for sm in self.results["social_media"]]
            self.results["ethical_report"].append(
                f"Social media-profielen ({', '.join(platforms)}) waren openbaar gelinkt of vindbaar."
            )
        
        if self.results["contact_form"]:
            self.results["ethical_report"].append(
                "Er is een contactformulier gevonden op de officiële website van het verblijf."
            )
        
        # Add GDPR compliance note
        self.results["ethical_report"].append(
            "Het gebruik van deze contactgegevens respecteert de AVG/GDPR omdat ze openbaar zijn gedeeld door de eigenaar voor zakelijke doeleinden."
        )
        
        # Add note if no information was found
        if not self.results["email_addresses"] and not self.results["social_media"] and not self.results["contact_form"]:
            self.results["ethical_report"].append(
                "Er is geen contactinformatie gevonden via openbare bronnen. Overweeg alternatieve zoektermen te proberen."
            )


#
# Reporting Functions
#

def format_contact_summary(results):
    """
    Format the contact information results into a readable summary.
    
    Args:
        results (dict): Results from the ContactFinder
        
    Returns:
        str: Formatted contact summary
    """
    property_info = results["property_info"]
    
    # Start with header
    summary = [
        "# Contact Information Summary",
        f"## Property: {property_info}",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "\n## Found Contact Information\n"
    ]
    
    # Add official website if found
    if results["official_website"]:
        summary.append(f"**Official Website:** {results['official_website']}")
    
    # Add email addresses if found
    if results["email_addresses"]:
        summary.append("\n**Email Addresses:**")
        for email in results["email_addresses"]:
            source_info = next((s for s in results["sources"] if s["type"] == "email" and s["value"] == email), None)
            source = f" (Found on: {source_info['source']})" if source_info else ""
            summary.append(f"- {email}{source}")
    
    # Add social media profiles if found
    if results["social_media"]:
        summary.append("\n**Social Media Profiles:**")
        for sm in results["social_media"]:
            platform = sm["platform"].capitalize()
            summary.append(f"- {platform}: {sm['url']}")
    
    # Add contact form if found
    if results["contact_form"]:
        summary.append(f"\n**Contact Form Available at:** {results['contact_form']}")
    
    # Add note if nothing found
    if not results["email_addresses"] and not results["social_media"] and not results["contact_form"]:
        summary.append("\n**No contact information found through public sources.**")
        summary.append("Consider trying alternative search terms or checking the suggestions below.")
    
    return "\n".join(summary)


def format_ethical_report(results):
    """
    Format the ethical considerations into a readable report.
    
    Args:
        results (dict): Results from the ContactFinder
        
    Returns:
        str: Formatted ethical report
    """
    # Start with header
    report = [
        "\n## Ethical Considerations\n"
    ]
    
    # Add ethical report points
    for point in results["ethical_report"]:
        report.append(f"- {point}")
    
    # Add suggestions if no information was found
    if not results["email_addresses"] and not results["social_media"] and not results["contact_form"]:
        report.append("\n### Suggestions for Further Research:")
        report.append("- Try searching with variations of the property name")
        report.append("- Search for the host name if known, along with the location")
        report.append("- Check if the property is part of a larger collection or management company")
        report.append("- Look for tourism board listings that might include the property")
        report.append("- Remember to only use publicly available information shared by the owner")
    
    return "\n".join(report)


def format_full_report(results):
    """
    Generate a complete report with all information.
    
    Args:
        results (dict): Results from the ContactFinder
        
    Returns:
        str: Complete formatted report
    """
    contact_summary = format_contact_summary(results)
    ethical_report = format_ethical_report(results)
    
    full_report = [
        contact_summary,
        ethical_report,
        "\n## Privacy Notice",
        "This information was collected ethically from public sources only.",
        "No information was scraped from Airbnb.com or obtained through non-public means.",
        "Always respect privacy laws and terms of service when contacting property owners."
    ]
    
    return "\n".join(full_report)


def save_report_to_file(results, filename):
    """
    Save the full report to a file.
    
    Args:
        results (dict): Results from the ContactFinder
        filename (str): Path to save the report
        
    Returns:
        str: Path to the saved file
    """
    report = format_full_report(results)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return filename


def save_results_json(results, filename):
    """
    Save the raw results to a JSON file.
    
    Args:
        results (dict): Results from the ContactFinder
        filename (str): Path to save the JSON
        
    Returns:
        str: Path to the saved file
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    return filename


#
# Simulation Functions for Demo
#

def _simulate_search(contact_finder, query):
    """
    Simulate a search for testing purposes.
    
    Args:
        contact_finder (ContactFinder): The contact finder instance
        query (str): The search query
    """
    # This is a simplified version of the search simulation from main.py
    if "casa azul" in query.lower():
        # Simulate finding a website for Casa Azul
        website_url = "https://www.casaazulportugal.com"
        contact_finder.results["official_website"] = website_url
        
        # Simulate extracting contact information
        contact_finder.results["email_addresses"] = ["info@casaazulportugal.com"]
        contact_finder.results["sources"].append({
            "type": "email",
            "value": "info@casaazulportugal.com",
            "source": website_url,
            "ethical_note": "Publicly displayed on official website"
        })
        
        # Simulate finding social media links
        contact_finder.results["social_media"].append({
            "platform": "instagram",
            "url": "https://www.instagram.com/casaazulportugal"
        })
        contact_finder.results["sources"].append({
            "type": "social_media",
            "value": "https://www.instagram.com/casaazulportugal",
            "source": website_url,
            "ethical_note": "Publicly linked from official website to instagram"
        })
        
        # Simulate finding contact form
        contact_finder.results["contact_form"] = f"{website_url}/contact"
        contact_finder.results["sources"].append({
            "type": "contact_form",
            "value": "Contact form available",
            "source": website_url,
            "ethical_note": "Contact form publicly available on official website"
        })
    elif "villa sunshine" in query.lower():
        # Simulate finding a website for Villa Sunshine
        website_url = "https://www.villasunshine.com"
        contact_finder.results["official_website"] = website_url
        
        # Simulate extracting contact information
        contact_finder.results["email_addresses"] = ["booking@villasunshine.com"]
        contact_finder.results["sources"].append({
            "type": "email",
            "value": "booking@villasunshine.com",
            "source": website_url,
            "ethical_note": "Publicly displayed on official website"
        })
        
        # Simulate finding a Facebook page
        fb_url = "https://www.facebook.com/VillaSunshineRentals"
        contact_finder.results["social_media"].append({
            "platform": "facebook",
            "url": fb_url
        })
        contact_finder.results["sources"].append({
            "type": "social_media",
            "value": fb_url,
            "source": "Direct search",
            "ethical_note": "Publicly available facebook profile"
        })
    
    # Generate ethical report
    contact_finder._generate_ethical_report()


#
# Flask Routes
#

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html', recent_searches=recent_searches[:5])


@app.route('/search', methods=['POST'])
def search():
    """Handle search form submission."""
    query = request.form.get('query', '').strip()
    
    if not query:
        return render_template('index.html', error="Please enter a search query.", recent_searches=recent_searches[:5])
    
    # Initialize contact finder
    contact_finder = ContactFinder()
    contact_finder.results["property_info"] = query
    
    # For demo purposes, we'll use the simulated search
    _simulate_search(contact_finder, query)
    
    # Generate report
    report = format_full_report(contact_finder.results)
    
    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    clean_name = clean_query(query).replace(" ", "_")[:30]
    report_filename = os.path.join(app.config['REPORTS_DIR'], f"{clean_name}_{timestamp}.md")
    json_filename = os.path.join(app.config['REPORTS_DIR'], f"{clean_name}_{timestamp}.json")
    
    save_report_to_file(contact_finder.results, report_filename)
    save_results_json(contact_finder.results, json_filename)
    
    # Add to recent searches
    search_record = {
        'query': query,
        'timestamp': timestamp,
        'report_file': os.path.basename(report_filename),
        'json_file': os.path.basename(json_filename),
        'has_email': len(contact_finder.results["email_addresses"]) > 0,
        'has_social': len(contact_finder.results["social_media"]) > 0,
        'has_website': contact_finder.results["official_website"] is not None,
    }
    recent_searches.insert(0, search_record)
    
    # Keep only the most recent 20 searches
    if len(recent_searches) > 20:
        recent_searches.pop()
    
    return render_template(
        'results.html',
        query=query,
        results=contact_finder.results,
        report=report,
        report_file=os.path.basename(report_filename),
        json_file=os.path.basename(json_filename)
    )


@app.route('/download/<filename>')
def download_file(filename):
    """Download a report file."""
    return send_file(os.path.join(app.config['REPORTS_DIR'], filename), as_attachment=True)


@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for searching."""
    data = request.json
    query = data.get('query', '').strip() if data else ''
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Initialize contact finder
    contact_finder = ContactFinder()
    contact_finder.results["property_info"] = query
    
    # For demo purposes, we'll use the simulated search
    _simulate_search(contact_finder, query)
    
    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    clean_name = clean_query(query).replace(" ", "_")[:30]
    json_filename = os.path.join(app.config['REPORTS_DIR'], f"{clean_name}_{timestamp}.json")
    save_results_json(contact_finder.results, json_filename)
    
    return jsonify({
        'query': query,
        'results': contact_finder.results,
        'json_file': os.path.basename(json_filename)
    })


@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')


@app.route('/privacy')
def privacy():
    """Render the privacy policy page."""
    return render_template('privacy.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
