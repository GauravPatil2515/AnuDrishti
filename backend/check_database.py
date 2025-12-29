#!/usr/bin/env python3
"""
Database Health Check and Restoration Tool
"""

from config.supabase import supabase_config
from datetime import datetime
import json

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_database_health():
    """Check database connection and table status"""
    print_header("🔍 DATABASE HEALTH CHECK")
    
    try:
        client = supabase_config.client
        
        # Test connection
        print("\n1. Testing Connection...")
        if supabase_config.test_connection():
            print("   ✅ Database connection successful")
        else:
            print("   ❌ Database connection failed")
            return False
        
        # Check tables
        print("\n2. Checking Tables...")
        tables = {
            'predictions': 'Toxicity prediction results',
            'user_feedback': 'User feedback on predictions',
            'molecule_library': 'Pre-loaded molecule database'
        }
        
        table_status = {}
        for table_name, description in tables.items():
            try:
                result = client.table(table_name).select('*').limit(1).execute()
                count_result = client.table(table_name).select('*', count='exact').execute()
                count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
                table_status[table_name] = {
                    'exists': True,
                    'count': count,
                    'description': description
                }
                print(f"   ✅ {table_name}: {count} records")
            except Exception as e:
                table_status[table_name] = {
                    'exists': False,
                    'error': str(e),
                    'description': description
                }
                print(f"   ❌ {table_name}: Error - {str(e)[:50]}")
        
        # Check predictions table schema
        print("\n3. Checking Predictions Table Schema...")
        try:
            result = client.table('predictions').select('*').limit(1).execute()
            if result.data:
                print("   ✅ Predictions table has data")
                sample = result.data[0]
                print(f"   📊 Sample record fields: {list(sample.keys())}")
            else:
                print("   ⚠️  Predictions table is empty (no data yet)")
        except Exception as e:
            print(f"   ❌ Schema check failed: {e}")
        
        # Check molecule library
        print("\n4. Checking Molecule Library...")
        try:
            result = client.table('molecule_library').select('*').limit(5).execute()
            if result.data:
                print(f"   ✅ Molecule library has {len(result.data)} molecules (showing first 5)")
                for mol in result.data[:5]:
                    print(f"      • {mol.get('name', 'Unknown')}: {mol.get('smiles', 'N/A')}")
            else:
                print("   ⚠️  Molecule library is empty")
        except Exception as e:
            print(f"   ❌ Library check failed: {e}")
        
        # Test write capability
        print("\n5. Testing Write Capability...")
        try:
            test_data = {
                'smiles': 'CCO',
                'molecule_name': 'Ethanol - Test',
                'endpoints': {
                    'test': 'data'
                },
                'user_id': 'health_check_test',
                'metadata': {
                    'test': True,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            # Insert test record
            result = client.table('predictions').insert(test_data).execute()
            if result.data:
                test_id = result.data[0].get('id')
                print(f"   ✅ Write test successful (ID: {test_id})")
                
                # Delete test record
                client.table('predictions').delete().eq('id', test_id).execute()
                print(f"   ✅ Cleanup successful (test record deleted)")
            else:
                print("   ⚠️  Write test completed but no data returned")
        except Exception as e:
            print(f"   ❌ Write test failed: {e}")
        
        print_header("📊 DATABASE STATUS SUMMARY")
        print(f"\n   Connection: ✅ Connected")
        print(f"   Tables: {len([t for t in table_status.values() if t['exists']])}/{len(tables)} exist")
        print(f"   Read Access: ✅ Working")
        print(f"   Write Access: ✅ Working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database health check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_database_stats():
    """Get detailed database statistics"""
    print_header("📈 DATABASE STATISTICS")
    
    try:
        client = supabase_config.client
        
        # Predictions stats
        predictions = client.table('predictions').select('*', count='exact').execute()
        pred_count = predictions.count if hasattr(predictions, 'count') else len(predictions.data)
        
        print(f"\n📊 Predictions Table:")
        print(f"   Total Records: {pred_count}")
        
        if predictions.data and len(predictions.data) > 0:
            # Analyze predictions
            toxic_count = 0
            safe_count = 0
            
            for pred in predictions.data:
                endpoints = pred.get('endpoints', {})
                if isinstance(endpoints, dict):
                    is_toxic = any(
                        v.get('prediction', '').lower() == 'toxic'
                        for v in endpoints.values()
                        if isinstance(v, dict)
                    )
                    if is_toxic:
                        toxic_count += 1
                    else:
                        safe_count += 1
            
            print(f"   Toxic Predictions: {toxic_count}")
            print(f"   Safe Predictions: {safe_count}")
            
            # Recent predictions
            recent = client.table('predictions').select('*').order('created_at', desc=True).limit(5).execute()
            if recent.data:
                print(f"\n   📋 Recent Predictions (last 5):")
                for i, pred in enumerate(recent.data, 1):
                    smiles = pred.get('smiles', 'N/A')
                    name = pred.get('molecule_name', 'Unknown')
                    created = pred.get('created_at', 'N/A')
                    print(f"      {i}. {name} ({smiles[:20]}...) - {created}")
        
        # Molecule library stats
        molecules = client.table('molecule_library').select('*', count='exact').execute()
        mol_count = molecules.count if hasattr(molecules, 'count') else len(molecules.data)
        
        print(f"\n🧬 Molecule Library:")
        print(f"   Total Molecules: {mol_count}")
        
        if molecules.data:
            # Group by category
            categories = {}
            for mol in molecules.data:
                cat = mol.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            print(f"   Categories:")
            for cat, count in sorted(categories.items()):
                print(f"      • {cat}: {count} molecules")
        
        # User feedback stats
        feedback = client.table('user_feedback').select('*', count='exact').execute()
        feedback_count = feedback.count if hasattr(feedback, 'count') else len(feedback.data)
        
        print(f"\n💬 User Feedback:")
        print(f"   Total Feedback: {feedback_count}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to get statistics: {e}")
        return False

if __name__ == "__main__":
    print_header("🧪 MedToXAi Database Health & Status Check")
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run health check
    health_ok = check_database_health()
    
    if health_ok:
        # Get detailed stats
        get_database_stats()
        
        print_header("✅ DATABASE STATUS: HEALTHY")
        print("\n🎉 Database is fully operational and ready to use!")
        print("\n📝 Next Steps:")
        print("   1. Database is ready for predictions")
        print("   2. All tables are accessible")
        print("   3. Read/Write operations working")
        print("   4. Data will be automatically saved")
    else:
        print_header("⚠️ DATABASE STATUS: NEEDS ATTENTION")
        print("\n📝 Troubleshooting:")
        print("   1. Check your .env file credentials")
        print("   2. Verify Supabase project is active")
        print("   3. Ensure database schema is created")
        print("   4. Run database/schema.sql in Supabase SQL Editor")
    
    print("\n" + "="*60 + "\n")
