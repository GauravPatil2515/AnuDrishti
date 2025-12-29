#!/usr/bin/env python3
"""
Environment Configuration Validator for MedToXAi
Validates all required environment variables are properly set
"""

import os
from dotenv import load_dotenv
from typing import List, Tuple

def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validate all required environment variables
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    # Load environment variables
    load_dotenv()
    
    errors = []
    warnings = []
    
    # Required environment variables
    required_vars = [
        ('GROQ_API_KEY', 'Groq AI API key for LLM functionality'),
        ('SUPABASE_URL', 'Supabase database URL'),
        ('SUPABASE_ANON_KEY', 'Supabase anonymous key for database access')
    ]
    
    # Optional but recommended variables
    optional_vars = [
        ('AI_MODEL', 'AI model name (defaults to llama3-8b-8192)'),
        ('FLASK_ENV', 'Flask environment (defaults to development)'),
        ('CORS_ORIGINS', 'CORS origins (defaults to http://localhost:3000)')
    ]
    
    print("🔍 MedToXAi Environment Validation")
    print("=" * 50)
    
    # Check required variables
    print("\n✅ Required Environment Variables:")
    for var_name, description in required_vars:
        value = os.getenv(var_name)
        if not value:
            errors.append(f"❌ {var_name}: Not set - {description}")
            print(f"❌ {var_name}: NOT SET")
        elif value.startswith('your-') or value == 'your-groq-api-key-here':
            errors.append(f"⚠️  {var_name}: Using placeholder value - {description}")
            print(f"⚠️  {var_name}: PLACEHOLDER VALUE")
        else:
            # Mask sensitive values
            masked_value = value[:8] + '...' if len(value) > 8 else value
            print(f"✅ {var_name}: {masked_value}")
    
    # Check optional variables
    print("\n📋 Optional Environment Variables:")
    for var_name, description in optional_vars:
        value = os.getenv(var_name)
        if not value:
            warnings.append(f"⚠️  {var_name}: Not set - {description}")
            print(f"⚠️  {var_name}: NOT SET (using default)")
        else:
            print(f"✅ {var_name}: {value}")
    
    # Configuration recommendations
    print("\n🎯 Configuration Recommendations:")
    
    ai_model = os.getenv('AI_MODEL', 'llama3-8b-8192')
    if 'gpt' in ai_model.lower():
        print("💡 Using GPT model - ensure Groq supports this model")
    elif 'llama' in ai_model.lower():
        print("💡 Using Llama model - good choice for chemistry/biology tasks")
    
    flask_env = os.getenv('FLASK_ENV', 'development')
    if flask_env == 'production':
        print("🔒 Production mode detected - ensure all security settings are configured")
        if not os.getenv('SECRET_KEY'):
            warnings.append("SECRET_KEY should be set for production")
    
    # Summary
    print("\n" + "=" * 50)
    if errors:
        print(f"❌ Validation Failed: {len(errors)} errors found")
        for error in errors:
            print(f"   {error}")
        return False, errors
    
    if warnings:
        print(f"⚠️  Validation Passed with {len(warnings)} warnings:")
        for warning in warnings:
            print(f"   {warning}")
    else:
        print("✅ All environment variables properly configured!")
    
    return True, []

def create_env_from_template():
    """Create .env file from .env.example if it doesn't exist"""
    if not os.path.exists('.env') and os.path.exists('.env.example'):
        import shutil
        shutil.copy('.env.example', '.env')
        print("📄 Created .env file from template")
        print("📝 Please edit .env file with your actual credentials")
        return True
    return False

if __name__ == "__main__":
    print("🚀 MedToXAi Environment Setup")
    print("=" * 50)
    
    # Create .env from template if needed
    if create_env_from_template():
        print("\n⚠️  Please configure your .env file before continuing")
        exit(1)
    
    # Validate environment
    is_valid, errors = validate_environment()
    
    if not is_valid:
        print(f"\n❌ Environment validation failed!")
        print("📝 Please check your .env file and fix the issues above")
        exit(1)
    
    print(f"\n🎉 Environment validation successful!")
    print("🚀 Your MedToXAi platform is ready to run!")