import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def get_ads_paper_pubdate(bibcode, api_token):
    """
    Retrieve the publication date of a paper using its NASA ADS bibcode.
    
    Parameters:
        bibcode (str): The NASA ADS bibcode of the paper.
        api_token (str): Your NASA ADS API token for authentication.
    
    Returns:
        str or None: The publication date of the paper in 'YYYY-MM-DD' format, or None if not found.
    """
    base_url = f"https://api.adsabs.harvard.edu/v1/search/query?"
    headers = {"Authorization": f"Bearer {api_token}"}
    params = {
        "q": f"bibcode:{bibcode}",
        "fl": "pubdate",
    }
    response = requests.get(base_url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if "pubdate" in data["response"]["docs"][0]:
            return data["response"]["docs"][0]["pubdate"]
    return None

def get_ads_citing_papers(bibcode, api_token, remove_false=True):
    """
    Get a DataFrame of papers citing the specified paper using its NASA ADS bibcode.
    
    Parameters:
        bibcode (str): The NASA ADS bibcode of the paper.
        api_token (str): Your NASA ADS API token for authentication.
        remove_false (bool): If True, remove papers with publication dates outside the range of the cited paper.
    
    Returns:
        pandas.DataFrame: A DataFrame containing citing papers with columns 'title', 'bibcode', 'year', 'month'.
    """
    base_url = "https://api.adsabs.harvard.edu/v1/search/query?"
    headers = {"Authorization": f"Bearer {api_token}"}

    if remove_false:
        now = datetime.today().strftime('%Y-%m-%d')
        cited_pubdate = get_ads_paper_pubdate(bibcode, api_token)
        if cited_pubdate is None:
            print("Unable to retrieve publication date of the cited paper.")
            return []
    
    params = {
        "q": f"citations({bibcode})",
        "fl": "title,bibcode,pubdate",
        "rows": 2000,  # You can adjust the number of rows as needed
        "start": 0,
        "sort": "date",
    }

    response = requests.get(base_url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        papers = pd.DataFrame(columns=['title', 'bibcode', 'year', 'month'])
        
        for paper in data["response"]["docs"]:
            title = paper["title"][0]
            bibcode = paper["bibcode"]
            pubdate = paper.get("pubdate", "Unknown")
            
            if remove_false:
                if (cited_pubdate is None) or (pubdate < cited_pubdate) or (pubdate > now):
                    continue
            
            year, month, _ = pubdate.split('-')
            year = int(year)
            month = int(month)
            if month == 0:
                month = 1
            
            papers.loc[len(papers.index)] = [title, bibcode, year, month]
        
        return papers
    else:
        print("Error:", response.status_code)
        return []

def plot_ADS_num_citations_by_time(bibcode, api_token, resolution='month'):
    """
    Plot the number of citations over time for a paper using its NASA ADS bibcode.
    
    Parameters:
        bibcode (str): The NASA ADS bibcode of the paper.
        api_token (str): Your NASA ADS API token for authentication.
        resolution (str): The time resolution for plotting ('month' or 'year').
    """
    citing_papers = get_ads_citing_papers(bibcode, api_token)
    group_cols = ['year']
    if resolution == 'month':
        group_cols.append('month')
    citing_papers.groupby(group_cols).title.count().plot(kind="bar")
    plt.legend([f'Citations by {resolution}'])
    plt.xlabel('Date')
    plt.xticks(rotation=0)
    plt.ylabel('Number of citations')
