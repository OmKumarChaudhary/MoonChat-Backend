import json
import os
import time

class CacheManager:
    def __init__(self, cache_dir='data'):
        self.cache_dir = cache_dir
        self._memory_cache = {}
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_file_path(self, key):
        return os.path.join(self.cache_dir, f"{key}.json")

    def get(self, key, ttl=300):
        """
        Retrieves data from memory or file if it's within the TTL (default 5 mins).
        """
        # 1. Check Memory Cache
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if time.time() - entry['timestamp'] < ttl:
                return entry['data']

        # 2. Check File Cache
        file_path = self._get_file_path(key)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    entry = json.load(f)
                    # Update memory cache
                    self._memory_cache[key] = entry
                    
                    if time.time() - entry['timestamp'] < ttl:
                        return entry['data']
            except Exception as e:
                print(f"Error reading cache file {key}: {e}")

        return None

    def set(self, key, data):
        """
        Saves data to both memory and a persistent JSON file.
        """
        entry = {
            'timestamp': time.time(),
            'data': data
        }
        
        # Save to memory
        self._memory_cache[key] = entry
        
        # Save to file
        file_path = self._get_file_path(key)
        try:
            with open(file_path, 'w') as f:
                json.dump(entry, f)
        except Exception as e:
            print(f"Error writing cache file {key}: {e}")

    def get_last_resort(self, key):
        """
        Returns whatever data is available in the cache (memory or file),
        even if it's expired. Useful for slow CPU/API failures.
        """
        if key in self._memory_cache:
            return self._memory_cache[key]['data']
            
        file_path = self._get_file_path(key)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    entry = json.load(f)
                    return entry['data']
            except Exception:
                pass
        return None

# Global instance for shared use
cache_manager = CacheManager()
