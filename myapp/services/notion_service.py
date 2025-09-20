import requests
from typing import Dict, List
import os
from dataclasses import dataclass
from notion_to_md import NotionToMarkdown
from notion_client import Client
import re

@dataclass
class NotionField:
    section: str
    block: str
    field_name: str
    field_type: str
    tooltip: str = ""

@dataclass
class FormField:
    key: str
    field_type: str
    label: str
    required: bool
    placeholder: str = ""
    options: List[Dict] = None
    validation_messages: Dict = None

class NotionClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def fetch_srd(self, id) -> List[NotionField]:
        blocks = []
        cursor = None
        
        while True:
            url = f"https://api.notion.com/v1/blocks/{id}/children"
            params = {}
            if cursor:
                params['start_cursor'] = cursor

            try:
                # We assume self.headers and the requests library are available as in your example
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()  # Raise an exception for bad status codes
                data = response.json()
                
                blocks.extend(data.get('results', []))
                
                # Check for pagination
                if data.get('has_more'):
                    cursor = data.get('next_cursor')
                else:
                    break  # Exit the loop if there are no more pages
                    
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page blocks: {e}")
                return []  # Return an empty list on error
        
        return blocks
    
    def notion_to_markdown(self, page_id):
        notion = Client(auth=self.token)
        n2m = NotionToMarkdown(notion)

        # Step 1: Convert the page into markdown blocks
        md_blocks = n2m.page_to_markdown(page_id)
        md_str = n2m.to_markdown_string(md_blocks).get('parent')

        # Step 2: Retrieve all blocks to find databases
        blocks = notion.blocks.children.list(page_id).get("results", [])

        for block in blocks:
            if block["type"] == "child_database":
                db_id = block["id"]

                # Step 3: Query database rows
                rows = notion.databases.query(db_id).get("results", [])

                if not rows:
                    continue

                # Step 4: Build Markdown table
                # Extract column headers from database properties
                props = list(rows[0]["properties"].keys())
                table_md = "| " + " | ".join(props) + " |\n"
                table_md += "|" + " --- |" * len(props) + "\n"

                # Add each row
                for row in rows:
                    row_cells = []
                    for prop in props:
                        cell = row["properties"][prop]
                        text_content = self.extract_text_from_property(cell)
                        row_cells.append(text_content)
                    table_md += "| " + " | ".join(row_cells) + " |\n"

                # Step 5: Append database table to Markdown
                md_str += f"\n\n### Database: {block['child_database']['title']}\n\n{table_md}"
        
        return md_str
    
    def extract_text_from_property(self, prop):
        """Helper to extract readable text from Notion property types."""
        if prop["type"] == "title":
            return " ".join([t["text"]["content"] for t in prop["title"]])
        elif prop["type"] == "rich_text":
            return " ".join([t["text"]["content"] for t in prop["rich_text"]])
        elif prop["type"] == "select":
            return prop["select"]["name"] if prop["select"] else ""
        elif prop["type"] == "multi_select":
            return ", ".join([s["name"] for s in prop["multi_select"]])
        elif prop["type"] == "number":
            return str(prop["number"]) if prop["number"] is not None else ""
        elif prop["type"] == "date":
            return prop["date"]["start"] if prop["date"] else ""
        elif prop["type"] == "checkbox":
            return "✅" if prop["checkbox"] else "❌"
        elif prop["type"] == "people":
            return ", ".join([p["name"] for p in prop["people"]])
        else:
            return ""

    def extract_diagram_images(self, srd_data: str):
        diagrams = ["Workflow selection", "Activity Diagram", "Use-case Diagram"]

        for diagram in diagrams:
            pattern = rf"{diagram}.*?!\[(.*?)\]\((.*?)\)"
            match = re.search(pattern, srd_data, re.IGNORECASE | re.DOTALL)

            if match:
                alt_text, image_url = match.groups()
                stripped_srd = re.sub(
                    rf"!\[{re.escape(alt_text)}\]\({re.escape(image_url)}\)",
                    "Image_placeholder",
                    srd_data,
                    count=1
                )
                epattern = r"!\[.*?\]\(.*?\)"
                updated_srd = re.sub(epattern, "", stripped_srd)
                return {
                    "name": diagram,
                    "image_url": image_url.strip(),
                    "updated_srd": updated_srd
                }

        return None

    def parse_block(self, block, count):
        block_type = block.get('type')

        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3"]:
            rich_text = block.get(block_type, {}).get('rich_text', [])
            return "".join([t.get('plain_text', '') for t in rich_text])

        elif block_type == "image":
            image_data = block.get('image', {})
            if image_data.get('type') == 'external':
                return {
                    "id": "image",
                    "image_data": image_data.get('external', {}).get('url')
                }
            else:
                return {
                    "id": "image",
                    "image_data": image_data.get('file', {}).get('url')
                }
        elif block_type in ["table", "table_row", "child_database"]:
            return {"id": block.get('id')}
        else:
            print("⚠️ Unhandled block type: %s, block: %s", block_type, block)
            return f"[Unhandled block type: {block_type}]"
        
    def download_image(self, url: str, filename: str):
        folder = os.path.join(os.getcwd(), "images")
        if not os.path.exists(folder):
            os.makedirs(folder)

        file_path = os.path.join(folder, f"{filename}.png")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print(f"✅ Saved: {filename}")

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch image: {e}")
            raise
        except IOError as e:
            print(f"Failed to write image to file: {e}")
            raise

    def structure_srd_data(self, pageId):
        blocks = self.fetch_srd(pageId)
        results = []
        count=0
        for block in blocks:
            content = self.parse_block(block, count)
            count+=1
            if isinstance(content, dict):
                if content['id'] != "image":
                    rows = self.fetch_srd(content['id'])
                    table_data = []
                    headers = []
                    for i, row in enumerate(rows):
                        cells = [
                            "".join([part.get('plain_text', '') for part in cell])
                            for cell in row.get('table_row', {}).get('cells', [])
                        ]

                        if i == 0:
                            # First row is the header
                            headers = cells
                        else:
                            # Create a dictionary from headers and row cells
                            row_object = {headers[j]: cells[j] if j < len(cells) else "" for j in range(len(headers))}
                            table_data.append(row_object)
                    results.append(table_data)
                else:
                    self.download_image(content["image_data"], results[-1] or f"{results[-1]}")
                    results.append('image_placeholder')
            else:
                results.append(content)
        
        return results
    
    def notion_to_json(self, blocks):
        simplified = []

        for block in blocks:
            block_type = block.get("type")
            item = {"id": block.get("id"), "type": block_type}

            if block_type in ["heading_1", "heading_2", "heading_3"]:
                texts = block[block_type].get("rich_text", [])
                item["text"] = " ".join([t["plain_text"] for t in texts])

            elif block_type == "paragraph":
                texts = block[block_type].get("rich_text", [])
                item["text"] = " ".join([t["plain_text"] for t in texts])

            elif block_type == "table":
                item["table"] = {
                    "columns": block["table"].get("table_width"),
                    "has_column_header": block["table"].get("has_column_header"),
                    "has_row_header": block["table"].get("has_row_header"),
                    "rows": []
                }

                # If you pass a function to fetch children, we can pull row data
                if self.fetch_srd:
                    children = self.fetch_srd(block["id"])
                    for row in children:
                        if row["type"] == "table_row":
                            cells = []
                            for cell in row["table_row"]["cells"]:
                                cell_text = " ".join(
                                    [t["plain_text"] for t in cell]
                                )
                                cells.append(cell_text)
                            item["table"]["rows"].append(cells)

            elif block_type == "child_database":
                item["title"] = block["child_database"].get("title")

            elif block_type == "image":
                file_obj = block["image"].get("file")
                if file_obj:
                    item["url"] = file_obj.get("url")

            if block.get("has_children"):
                item["has_children"] = True

            simplified.append(item)

        return simplified