#!/usr/bin/env python3
"""
Memory Server Interactive Testing Tool
=====================================

Interactive tool for testing Memory Server from VSCode terminal.
"""

import requests
import json
import time
import sys
from typing import Dict, Any


class MemoryServerTester:
    """Interactive tester for Memory Server"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_connection(self) -> bool:
        """Test if server is running"""
        try:
            response = self.session.get(f"{self.base_url}/health/")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
    
    def pretty_print(self, data: Dict[str, Any], title: str = ""):
        """Pretty print JSON response"""
        if title:
            print(f"\n{'='*50}")
            print(f"🔍 {title}")
            print('='*50)
        
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
    
    def health_check(self):
        """Check server health"""
        response = self.session.get(f"{self.base_url}/health/")
        self.pretty_print(response.json(), "Health Check")
        
        # Also check detailed health
        response = self.session.get(f"{self.base_url}/health/detailed")
        self.pretty_print(response.json(), "Detailed Health")
    
    def system_info(self):
        """Get system information"""
        response = self.session.get(f"{self.base_url}/")
        self.pretty_print(response.json(), "System Information")
    
    def list_workspaces(self):
        """List available workspaces"""
        response = self.session.get(f"{self.base_url}/api/v1/documents/workspaces")
        self.pretty_print(response.json(), "Available Workspaces")
    
    def document_stats(self):
        """Get document statistics"""
        response = self.session.get(f"{self.base_url}/api/v1/documents/stats")
        self.pretty_print(response.json(), "Document Statistics")
    
    def create_test_document(self):
        """Create a test document"""
        doc_data = {
            "title": "Interactive Test Document",
            "content": """
            Este es un documento de prueba creado desde VSCode.
            Contiene información sobre:
            - Inteligencia Artificial
            - Machine Learning  
            - Procesamiento de Lenguaje Natural
            - Memory Server funcionando correctamente
            
            El sistema está operativo y responde a las peticiones.
            """,
            "metadata": {
                "source": "vscode-interactive",
                "category": "testing",
                "tags": ["ai", "ml", "nlp", "test"],
                "created_from": "VSCode terminal"
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/documents/workspace/test",
            json=doc_data
        )
        
        print(f"Status Code: {response.status_code}")
        try:
            self.pretty_print(response.json(), "Document Creation")
        except:
            print(f"Response: {response.text}")
    
    def search_documents(self, query: str = "inteligencia artificial"):
        """Search documents"""
        params = {"query": query, "workspace": "test"}
        response = self.session.get(
            f"{self.base_url}/api/v1/documents/search",
            params=params
        )
        
        print(f"Search Query: '{query}'")
        print(f"Status Code: {response.status_code}")
        try:
            self.pretty_print(response.json(), "Document Search Results")
        except:
            print(f"Response: {response.text}")
    
    def test_web_search(self, query: str = "Python machine learning"):
        """Test web search (will show API key error)"""
        search_data = {
            "query": query,
            "max_results": 3
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/search/web",
            json=search_data
        )
        
        print(f"Web Search Query: '{query}'")
        self.pretty_print(response.json(), "Web Search Results")
    
    def test_summarization(self):
        """Test content summarization"""
        content_data = {
            "content": """
            La inteligencia artificial (IA) es una tecnología revolucionaria que está 
            transformando múltiples sectores. El machine learning, una rama de la IA,
            permite a las máquinas aprender patrones de datos sin programación explícita.
            
            El procesamiento de lenguaje natural (NLP) facilita la comunicación entre
            humanos y máquinas mediante texto y voz. Los modelos de deep learning
            han logrado avances significativos en visión por computadora.
            
            Los sistemas de memoria como este Memory Server permiten el almacenamiento
            y recuperación eficiente de información contextual.
            """,
            "summary_type": "brief"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/documents/summarize/content",
            json=content_data
        )
        
        print(f"Status Code: {response.status_code}")
        try:
            self.pretty_print(response.json(), "Content Summarization")
        except:
            print(f"Response: {response.text}")
    
    def log_activity(self):
        """Log test activity"""
        activity_data = {
            "action": "interactive_test",
            "details": "Testing Memory Server from VSCode interactive tool"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/documents/activity",
            json=activity_data
        )
        
        print(f"Status Code: {response.status_code}")
        try:
            self.pretty_print(response.json(), "Activity Logged")
        except:
            print(f"Response: {response.text}")
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Memory Server Comprehensive Test")
        print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not self.test_connection():
            print("❌ ERROR: Cannot connect to Memory Server")
            print("Make sure the server is running on http://127.0.0.1:8001")
            return False
        
        print("✅ Connection established")
        
        # Run all tests
        tests = [
            ("Health Check", self.health_check),
            ("System Info", self.system_info),
            ("List Workspaces", self.list_workspaces),
            ("Document Stats", self.document_stats),
            ("Create Test Document", self.create_test_document),
            ("Search Documents", self.search_documents),
            ("Web Search Test", self.test_web_search),
            ("Summarization Test", self.test_summarization),
            ("Log Activity", self.log_activity)
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\n🧪 Running: {test_name}")
                test_func()
                print(f"✅ {test_name} completed")
            except Exception as e:
                print(f"❌ {test_name} failed: {e}")
        
        print(f"\n🎉 Comprehensive test completed!")
        return True
    
    def interactive_menu(self):
        """Interactive menu for testing"""
        while True:
            print("\n" + "="*60)
            print("🧪 MEMORY SERVER INTERACTIVE TESTER")
            print("="*60)
            print("1. Health Check")
            print("2. System Information")
            print("3. List Workspaces")
            print("4. Document Statistics")
            print("5. Create Test Document")
            print("6. Search Documents")
            print("7. Web Search Test")
            print("8. Content Summarization")
            print("9. Log Activity")
            print("10. Run All Tests")
            print("0. Exit")
            print("-"*60)
            
            choice = input("Select option (0-10): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                self.health_check()
            elif choice == "2":
                self.system_info()
            elif choice == "3":
                self.list_workspaces()
            elif choice == "4":
                self.document_stats()
            elif choice == "5":
                self.create_test_document()
            elif choice == "6":
                query = input("Enter search query (default: 'inteligencia artificial'): ").strip()
                self.search_documents(query or "inteligencia artificial")
            elif choice == "7":
                query = input("Enter web search query (default: 'Python machine learning'): ").strip()
                self.test_web_search(query or "Python machine learning")
            elif choice == "8":
                self.test_summarization()
            elif choice == "9":
                self.log_activity()
            elif choice == "10":
                self.run_comprehensive_test()
            else:
                print("❌ Invalid option")
            
            input("\nPress Enter to continue...")


def main():
    """Main function"""
    tester = MemoryServerTester()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Run comprehensive test automatically
        tester.run_comprehensive_test()
    else:
        # Interactive menu
        tester.interactive_menu()


if __name__ == "__main__":
    main()