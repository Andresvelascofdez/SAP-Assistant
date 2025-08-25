#!/usr/bin/env python3
"""
Script de verificación de dependencias
Wiki Inteligente SAP IS-U
"""

import sys
import importlib
import subprocess
from typing import List, Dict, Tuple

# Lista de dependencias requeridas con sus versiones mínimas
REQUIRED_PACKAGES = {
    # Core framework
    "fastapi": "0.104.0",
    "uvicorn": "0.24.0",
    "pydantic": "2.5.0",
    "pydantic_settings": "2.1.0",
    
    # Database
    "sqlalchemy": "2.0.0",
    "asyncpg": "0.29.0",
    "alembic": "1.13.0",
    
    # AI/ML
    "openai": "1.3.0",
    "tiktoken": "0.5.0",
    "qdrant_client": "1.7.0",
    
    # Security
    "python_jose": "3.3.0",
    "passlib": "1.7.4",
    "python_multipart": "0.0.6",
    "bcrypt": "4.1.0",
    
    # Utilities
    "requests": "2.31.0",
    "aiofiles": "23.2.0",
    "python_docx": "1.1.0",
    "pypdf2": "3.0.0",
    "beautifulsoup4": "4.12.0",
    "markdown": "3.5.0",
    
    # Rate limiting
    "slowapi": "0.1.9",
    "redis": "5.0.0",
    
    # Scheduling
    "apscheduler": "3.10.0",
    
    # Testing
    "pytest": "7.4.0",
    "pytest_asyncio": "0.21.0",
    "pytest_cov": "4.1.0",
    "httpx": "0.25.0",
    
    # Development
    "black": "23.12.0",
    "flake8": "6.1.0",
    "isort": "5.13.0"
}

class DependencyChecker:
    """Verificador de dependencias"""
    
    def __init__(self):
        self.missing_packages = []
        self.outdated_packages = []
        self.installed_packages = []
    
    def check_package(self, package_name: str, min_version: str) -> Tuple[bool, str]:
        """Verificar si un paquete está instalado y actualizado"""
        try:
            # Mapear nombres de paquetes especiales
            import_name = self._get_import_name(package_name)
            
            # Intentar importar
            module = importlib.import_module(import_name)
            
            # Obtener versión si está disponible
            version = getattr(module, '__version__', 'unknown')
            
            # Verificar versión mínima (simplificado)
            if version != 'unknown' and self._compare_versions(version, min_version):
                return True, version
            else:
                return True, f"{version} (min: {min_version})"
                
        except ImportError:
            return False, "Not installed"
    
    def _get_import_name(self, package_name: str) -> str:
        """Mapear nombres de paquetes a nombres de import"""
        mapping = {
            "python_jose": "jose",
            "python_multipart": "multipart",
            "python_docx": "docx",
            "pypdf2": "PyPDF2",
            "beautifulsoup4": "bs4",
            "pydantic_settings": "pydantic_settings"
        }
        return mapping.get(package_name, package_name)
    
    def _compare_versions(self, current: str, minimum: str) -> bool:
        """Comparar versiones (simplificado)"""
        try:
            current_parts = [int(x) for x in current.split('.')]
            minimum_parts = [int(x) for x in minimum.split('.')]
            
            # Rellenar con ceros si es necesario
            max_len = max(len(current_parts), len(minimum_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            minimum_parts.extend([0] * (max_len - len(minimum_parts)))
            
            return current_parts >= minimum_parts
        except:
            return True  # Asumir que está bien si no podemos comparar
    
    def check_all_dependencies(self) -> Dict[str, Dict]:
        """Verificar todas las dependencias"""
        print("🔍 Verificando dependencias del proyecto...")
        print("=" * 60)
        
        results = {}
        
        for package, min_version in REQUIRED_PACKAGES.items():
            is_installed, version_info = self.check_package(package, min_version)
            
            status = "✅" if is_installed else "❌"
            category = "Core" if package in ["fastapi", "uvicorn", "sqlalchemy"] else "Optional"
            
            if package in ["openai", "qdrant_client", "tiktoken"]:
                category = "AI/ML"
            elif package in ["pytest", "black", "flake8"]:
                category = "Development"
            
            results[package] = {
                "installed": is_installed,
                "version": version_info,
                "required": min_version,
                "category": category,
                "status": status
            }
            
            if is_installed:
                self.installed_packages.append(package)
            else:
                self.missing_packages.append(package)
            
            print(f"{status} {package:20} | {version_info:15} | {category}")
        
        return results
    
    def generate_install_commands(self) -> List[str]:
        """Generar comandos de instalación para paquetes faltantes"""
        if not self.missing_packages:
            return []
        
        # Comandos por categoría
        commands = []
        
        # Core packages (críticos)
        core_packages = [p for p in self.missing_packages 
                        if p in ["fastapi", "uvicorn", "sqlalchemy", "pydantic", "asyncpg"]]
        if core_packages:
            commands.append(f"pip install {' '.join(core_packages)}")
        
        # AI/ML packages
        ai_packages = [p for p in self.missing_packages 
                      if p in ["openai", "tiktoken", "qdrant_client"]]
        if ai_packages:
            commands.append(f"pip install {' '.join(ai_packages)}")
        
        # Security packages
        security_packages = [p for p in self.missing_packages 
                           if p in ["python_jose", "passlib", "bcrypt"]]
        if security_packages:
            commands.append(f"pip install {' '.join(security_packages)}")
        
        # Utility packages
        util_packages = [p for p in self.missing_packages 
                        if p not in core_packages + ai_packages + security_packages]
        if util_packages:
            commands.append(f"pip install {' '.join(util_packages)}")
        
        return commands
    
    def create_requirements_file(self) -> None:
        """Crear archivo requirements.txt actualizado"""
        with open("requirements_verified.txt", "w") as f:
            f.write("# Requirements verificados para Wiki Inteligente SAP IS-U\n")
            f.write("# Generado automáticamente\n\n")
            
            categories = {
                "Core": [],
                "AI/ML": [],
                "Security": [],
                "Development": [],
                "Optional": []
            }
            
            for package, min_version in REQUIRED_PACKAGES.items():
                category = "Core" if package in ["fastapi", "uvicorn", "sqlalchemy"] else "Optional"
                if package in ["openai", "qdrant_client", "tiktoken"]:
                    category = "AI/ML"
                elif package in ["python_jose", "passlib", "bcrypt"]:
                    category = "Security"
                elif package in ["pytest", "black", "flake8"]:
                    category = "Development"
                
                categories[category].append(f"{package}>={min_version}")
            
            for category, packages in categories.items():
                if packages:
                    f.write(f"\n# {category}\n")
                    for package in sorted(packages):
                        f.write(f"{package}\n")
        
        print("\n📄 Archivo 'requirements_verified.txt' creado")


def main():
    """Función principal"""
    print("🔍 Wiki Inteligente SAP IS-U - Verificador de Dependencias")
    print("=" * 60)
    
    checker = DependencyChecker()
    results = checker.check_all_dependencies()
    
    print(f"\n📊 Resumen:")
    print(f"   ✅ Instalados: {len(checker.installed_packages)}")
    print(f"   ❌ Faltantes:  {len(checker.missing_packages)}")
    print(f"   📦 Total:      {len(REQUIRED_PACKAGES)}")
    
    if checker.missing_packages:
        print(f"\n🔧 Paquetes faltantes:")
        for package in checker.missing_packages:
            category = "CRÍTICO" if package in ["fastapi", "uvicorn", "sqlalchemy"] else "opcional"
            print(f"   - {package} ({category})")
        
        print(f"\n💾 Comandos de instalación:")
        commands = checker.generate_install_commands()
        for i, cmd in enumerate(commands, 1):
            print(f"   {i}. {cmd}")
        
        print(f"\n📦 O instalar todo de una vez:")
        print(f"   pip install -r requirements.txt")
    
    # Crear archivo de requirements verificado
    checker.create_requirements_file()
    
    print(f"\n🚀 Estado del proyecto:")
    if len(checker.missing_packages) == 0:
        print("   ✅ Todas las dependencias están instaladas!")
        print("   ✅ El proyecto está listo para ejecutarse")
    elif any(p in checker.missing_packages for p in ["fastapi", "uvicorn", "sqlalchemy"]):
        print("   ⚠️  Faltan dependencias CRÍTICAS")
        print("   ❌ El proyecto NO puede ejecutarse")
    else:
        print("   ⚠️  Faltan algunas dependencias opcionales")
        print("   🟡 El proyecto puede ejecutarse con funcionalidad limitada")
    
    print(f"\n📋 Para instalar dependencias faltantes:")
    print(f"   1. Windows: .\\install.ps1")
    print(f"   2. Linux:   ./install.sh") 
    print(f"   3. Manual:  pip install -r requirements.txt")


if __name__ == "__main__":
    main()
