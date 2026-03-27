const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.0.100:5000';

export interface User {
  id: number;
  name: string;
  registration: string;
  cpf?: string;
  idface_id?: number;
  active: boolean;
  has_photo: boolean;
  photo_url?: string;
  created_at: string;
}

export interface Presence {
  id: number;
  user_id: number;
  name: string;
  registration: string;
  timestamp: string;
  created_at: string;
  entries_count: number;
}

export interface Stats {
  total_users: number;
  present_today: number;
  absent_today: number;
  total_entries_today: number;
}

export interface CreateUserData {
  name: string;
  registration: string;
  cpf?: string;
  photo?: string;
}

export const api = {
  async getUsers(): Promise<User[]> {
    const response = await fetch(`${API_BASE_URL}/api/users?t=${Date.now()}`);
    const data = await response.json();
    return data.users;
  },

  async getUser(id: number): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}`);
    const data = await response.json();
    return data.user;
  },

  async getRecognitions(limit: number = 100): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/api/recognitions?limit=${limit}`);
    const data = await response.json();
    return data.recognitions || [];
  },

  async createUser(userData: CreateUserData): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao criar usuário');
    }
    return data.user;
  },

  async updateUser(id: number, userData: Partial<CreateUserData>): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao atualizar usuário');
    }
    return data.user;
  },

  async deleteUser(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}`, {
      method: 'DELETE',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao excluir usuário');
    }
  },

  async deleteUserPhoto(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}/photo`, {
      method: 'DELETE',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao excluir foto');
    }
  },

  async syncUser(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}/sync`, {
      method: 'POST',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao sincronizar');
    }
  },

  async toggleUserStatus(id: number): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}/toggle-status`, {
      method: 'POST',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao alterar status');
    }
    return data.active;
  },

  async syncUser(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}/sync`, {
      method: 'POST',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao sincronizar usuário');
    }
  },

  async checkUserSync(id: number): Promise<{ synced: boolean; reason?: string }> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}/check-sync`);
    const data = await response.json();
    return { synced: data.synced, reason: data.reason };
  },

  async syncUserToIdFace(id: number): Promise<{ success: boolean; error?: string }> {
    const response = await fetch(`${API_BASE_URL}/api/users/${id}/sync`, { method: 'POST' });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao sincronizar');
    }
    return { success: true };
  },

  async syncAllPendingUsers(force: boolean = true): Promise<{ success_count: number; error_count: number }> {
    const response = await fetch(`${API_BASE_URL}/api/users/sync-pending`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force }),
    });
    const data = await response.json();
    return { success_count: data.success_count, error_count: data.error_count };
  },

  async syncFromIdFace(): Promise<{ synced: number; details: { action: string; name: string }[] }> {
    const response = await fetch(`${API_BASE_URL}/api/users/sync-all?t=${Date.now()}`, { method: 'POST' });
    const data = await response.json();
    return { synced: data.synced, details: data.details };
  },

  async syncAllUsers(): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/sync-all`, {
      method: 'POST',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao sincronizar usuários');
    }
    return data;
  },

  async getPresenceToday(): Promise<{ presence: Presence[]; stats: Stats }> {
    const response = await fetch(`${API_BASE_URL}/api/presence/today`);
    const data = await response.json();
    return { presence: data.presence, stats: data.stats };
  },

  async getRecentPresence(limit: number = 50): Promise<Presence[]> {
    const response = await fetch(`${API_BASE_URL}/api/presence/recent?limit=${limit}`);
    const data = await response.json();
    return data.presence;
  },

  async getPresenceStats(): Promise<Stats> {
    const response = await fetch(`${API_BASE_URL}/api/presence/stats`);
    const data = await response.json();
    return data.stats;
  },

  async testIdFace(): Promise<{ connected: boolean; session: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/idface/test`);
    return response.json();
  },

  async openDoor(door: number = 0): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/idface/door/open`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ door }),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error('Erro ao abrir porta');
    }
  },

  getUserPhotoUrl(userId: number): string {
    return `${API_BASE_URL}/api/users/${userId}/photo`;
  },

  async importUsersCSV(file: File): Promise<{ count: number; users: { name: string; registration: string; cpf?: string }[] }> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/users/import-csv`, {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao importar CSV');
    }
    return { count: data.count, users: data.users };
  },

  async batchCreateUsers(users: { name: string; registration: string; cpf?: string; photo?: string }[]): Promise<{
    success_count: number;
    error_count: number;
    results: { registration: string; name: string; success: boolean; error?: string }[];
  }> {
    const response = await fetch(`${API_BASE_URL}/api/users/batch-create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ users }),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao criar usuários em lote');
    }
    return {
      success_count: data.success_count,
      error_count: data.error_count,
      results: data.results,
    };
  },

  async getDevices(): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/api/devices`);
    const data = await response.json();
    return data.devices || [];
  },

  async createDevice(deviceData: { name: string; ip: string; port: number; user: string; password: string }): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/devices`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(deviceData),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao criar dispositivo');
    }
    return data.device;
  },

  async updateDevice(id: number, deviceData: { name?: string; ip?: string; port?: number; user?: string; password?: string; active?: boolean }): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/devices/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(deviceData),
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao atualizar dispositivo');
    }
    return data.device;
  },

  async deleteDevice(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/devices/${id}`, {
      method: 'DELETE',
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Erro ao excluir dispositivo');
    }
  },

  async testDeviceConnection(id: number): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/devices/${id}/test`, {
      method: 'POST',
    });
    return response.json();
  },

  async testNewDeviceConnection(ip: string, port: number, user: string, password: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/devices/test-connection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip, port, user, password }),
    });
    return response.json();
  },
};
