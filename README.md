# Berar API Gateway

A Django-based API Gateway for managing roles, permissions, and menus in the Berar system.

---

## Features

- **Role Management:** Create, update, and soft-delete roles.
- **Permission Management:** Assign permissions to roles for specific menus, with soft delete support.
- **Menu Management:** Manage application menus and their access.
- **Soft Delete:** Records are soft deleted using `deleted_at` and `deleted_by` fields.

---



## Setup Instructions

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/berar_api_gateway.git
   cd berar_api_gateway
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Apply migrations:**
   ```sh
   python manage.py makemigrations
   python manage.py migrate
   ```

---

## Seeding Data

You can seed data using individual commands or a single combined command:

### **Single Seeder Command (Recommended)**
Run all seeders (admin user, menus, admin role & permissions) in order:
```sh
python manage.py seed_all
```
This will:
- Create the admin user
- Create default menus
- Create the admin role and assign all permissions for all menus to the admin role

### **Individual Seeder Commands**
You can also run each seeder separately if needed:
```sh
python manage.py seed_user
python manage.py seed_menu
python manage.py seed_admin_role_permission
```

### **(Optional) Seed additional data:**
```sh
python manage.py loaddata <your_seed_file>.json
```

---

## Run the Development Server

```sh
python manage.py runserver
```

---

## Usage

- Use the provided API endpoints to manage roles, permissions, and menus.
- Permissions are soft deleted before new ones are created for the same role/menu.
- The `.gitignore` file is set up to exclude Python bytecode, virtual environments, logs, and IDE files.

---

## Notes

- **Soft Delete:**  
  The system uses soft delete for permissions. If you want to enforce uniqueness only for active permissions, consider using a partial unique index (PostgreSQL only).

- **Unique Constraints:**  
  If you use only soft delete, remove the unique constraint from the model to avoid integrity errors.

---

## Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Create a new Pull Request.

---

## License

This project is licensed under the MIT License.