"""
Program to scrape pictures from pexels.com using its api
Sources:
- https://www.learnpythonwithrune.org/from-zero-to-creating-photo-mosaic-using-faces-with-opencv/

    To get key: sign up for pexels https://www.pexels.com/join/
    Reguest key : https://www.pexels.com/api/
    - No need to set URL
    - Accept email send to you
    - Refresh API or see key here: https://www.pexels.com/api/new/
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union
from pathlib import Path
import requests


# import 3rd-party modules
from pexels_api import API


# import local modules

# =====================================================================
# Define functions
# =====================================================================

def scrape(api_key, query, max_imgs_count):
    """
    Function to scrape pexels.com using its api
    """
    # set directory where to save the images
    img_dir = Path("/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/assets/images/pexels") / query

    # make directory if doesn't exist
    img_dir.mkdir(parents=True, exist_ok=True)

    # access api
    api = API(api_key)

    # run a search query
    api.search(query)

    # photos = api.get_entries()
    print("Search: ", query)
    print("Total search results: ", api.total_results)
    print("Fetching max number of images: ", max_imgs_count)
    
    # initialize counter
    count = 0

    while True:

        # get image entries
        imgs = api.get_entries()

        # print number of images in page
        print(len(imgs))

        # break loop if no image
        if len(imgs) == 0:
            break

        # loop over each image in page
        for img in imgs:

            # set image path 
            img_path = img_dir / f"{img.photographer}_{count:05d}.{img.original.split('.')[-1]}"
            print(img_path)
            
            # request image
            img_request = requests.get(img.original)

            # write image to disk if successfull request 
            if img_request.status_code == 200:
                with open(img_path, 'wb') as f:
                    f.write(img_request.content)

            # incrementer counter by 1
            count += 1

            # return if count of max images is reached
            if count >= max_imgs_count:
                return

        # return if count of max images is reached
        if count >= max_imgs_count:
            return

        # return if no next page
        if not api.has_next_page:
            print("Last page: ", api.page)
            return

        # search next page
        api.search_next_page()



# =====================================================================
# Define classes
# =====================================================================


# =====================================================================
# Run demo
# =====================================================================

# run demo if this py file is run
if __name__ == "__main__":

    # declare constants & variables
    PEXELS_API_KEY = '563492ad6f917000010000018c564df5494446bfb293fda6dc3d57b3'
    QUERY = 'diversity'
    MAX_IMGS = 2000

    # scrape images
    scrape(PEXELS_API_KEY, QUERY, MAX_IMGS)