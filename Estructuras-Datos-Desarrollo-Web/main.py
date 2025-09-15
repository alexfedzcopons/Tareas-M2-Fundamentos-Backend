
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class NodoProducto:
    def __init__(self, producto_id: int, nombre: str, precio: float, stock: int):
        self.producto_id = producto_id
        self.nombre = nombre
        self.precio = precio
        self.stock = stock
        self.izquierda = None
        self.derecha = None

class ArbolProductos:
    def __init__(self):
        self.raiz = None
        self.contador = 0
    
    def insertar(self, producto_id: int, nombre: str, precio: float, stock: int):
        if self.buscar(producto_id) is not None:
            raise ValueError(f"El producto con ID {producto_id} ya existe")
        
        if self.raiz is None:
            self.raiz = NodoProducto(producto_id, nombre, precio, stock)
        else:
            self._insertar_recursivo(self.raiz, producto_id, nombre, precio, stock)
        self.contador += 1
    
    def _insertar_recursivo(self, nodo, producto_id, nombre, precio, stock):
        if producto_id < nodo.producto_id:
            if nodo.izquierda is None:
                nodo.izquierda = NodoProducto(producto_id, nombre, precio, stock)
            else:
                self._insertar_recursivo(nodo.izquierda, producto_id, nombre, precio, stock)
        elif producto_id > nodo.producto_id:
            if nodo.derecha is None:
                nodo.derecha = NodoProducto(producto_id, nombre, precio, stock)
            else:
                self._insertar_recursivo(nodo.derecha, producto_id, nombre, precio, stock)
    
    def buscar(self, producto_id: int):
        return self._buscar_recursivo(self.raiz, producto_id)
    
    def _buscar_recursivo(self, nodo, producto_id):
        if nodo is None:
            return None
        if producto_id == nodo.producto_id:
            return nodo
        elif producto_id < nodo.producto_id:
            return self._buscar_recursivo(nodo.izquierda, producto_id)
        else:
            return self._buscar_recursivo(nodo.derecha, producto_id)
    
    def listar_todos(self):
        productos = []
        self._recorrer_inorden(self.raiz, productos)
        return productos
    
    def _recorrer_inorden(self, nodo, productos):
        if nodo is not None:
            self._recorrer_inorden(nodo.izquierda, productos)
            producto_dict = {
                "producto_id": nodo.producto_id,
                "nombre": nodo.nombre,
                "precio": nodo.precio,
                "stock": nodo.stock
            }
            productos.append(producto_dict)
            self._recorrer_inorden(nodo.derecha, productos)


class ItemPedido:
    def __init__(self, producto_id: int, cantidad: int, precio_unitario: float):
        self.producto_id = producto_id
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario
        self.subtotal = cantidad * precio_unitario

class NodoPedido:
    def __init__(self, pedido_id: int, cliente: str, items: List[ItemPedido]):
        self.pedido_id = pedido_id
        self.cliente = cliente
        self.items = items
        self.fecha_creacion = datetime.now()
        self.total = sum(item.subtotal for item in items)
        self.siguiente = None

class ListaPedidos:
    def __init__(self):
        self.cabeza = None
        self.contador = 0
    
    def agregar_pedido(self, pedido_id: int, cliente: str, items: List[ItemPedido]):
        if self.buscar_pedido(pedido_id) is not None:
            raise ValueError(f"Ya existe un pedido con ID {pedido_id}")
        
        nuevo_nodo = NodoPedido(pedido_id, cliente, items)
        
        if self.cabeza is None:
            self.cabeza = nuevo_nodo
        else:
            actual = self.cabeza
            while actual.siguiente is not None:
                actual = actual.siguiente
            actual.siguiente = nuevo_nodo
        
        self.contador += 1
        return nuevo_nodo
    
    def buscar_pedido(self, pedido_id: int):
        actual = self.cabeza
        while actual is not None:
            if actual.pedido_id == pedido_id:
                return actual
            actual = actual.siguiente
        return None
    
    def eliminar_pedido(self, pedido_id: int):
        if self.cabeza is None:
            return False
        
        if self.cabeza.pedido_id == pedido_id:
            self.cabeza = self.cabeza.siguiente
            self.contador -= 1
            return True
        
        actual = self.cabeza
        while actual.siguiente is not None:
            if actual.siguiente.pedido_id == pedido_id:
                actual.siguiente = actual.siguiente.siguiente
                self.contador -= 1
                return True
            actual = actual.siguiente
        return False
    
    def listar_todos_pedidos(self):
        pedidos = []
        actual = self.cabeza
        
        while actual is not None:
            pedido_dict = {
                "pedido_id": actual.pedido_id,
                "cliente": actual.cliente,
                "fecha_creacion": actual.fecha_creacion.isoformat(),
                "total": actual.total,
                "items": [
                    {
                        "producto_id": item.producto_id,
                        "cantidad": item.cantidad,
                        "precio_unitario": item.precio_unitario,
                        "subtotal": item.subtotal
                    }
                    for item in actual.items
                ]
            }
            pedidos.append(pedido_dict)
            actual = actual.siguiente
        return pedidos
    
    def actualizar_pedido(self, pedido_id: int, nuevo_cliente: str = None, nuevos_items: List[ItemPedido] = None):
        nodo = self.buscar_pedido(pedido_id)
        if nodo is None:
            return False
        
        if nuevo_cliente:
            nodo.cliente = nuevo_cliente
        if nuevos_items:
            nodo.items = nuevos_items
            nodo.total = sum(item.subtotal for item in nuevos_items)
        return True

arbol_productos = ArbolProductos()
lista_pedidos = ListaPedidos()


class ProductoCreate(BaseModel):
    producto_id: int
    nombre: str
    precio: float
    stock: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "producto_id": 101,
                "nombre": "Laptop HP",
                "precio": 599.99,
                "stock": 15
            }
        }

class Producto(BaseModel):
    producto_id: int
    nombre: str
    precio: float
    stock: int

class ItemPedidoCreate(BaseModel):
    producto_id: int
    cantidad: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "producto_id": 50,
                "cantidad": 2
            }
        }

class PedidoCreate(BaseModel):
    pedido_id: int
    cliente: str
    items: List[ItemPedidoCreate]
    
    class Config:
        json_schema_extra = {
            "example": {
                "pedido_id": 1001,
                "cliente": "Juan Pérez",
                "items": [
                    {"producto_id": 50, "cantidad": 2},
                    {"producto_id": 30, "cantidad": 1}
                ]
            }
        }

class ItemPedidoResponse(BaseModel):
    producto_id: int
    cantidad: int
    precio_unitario: float
    subtotal: float

class PedidoResponse(BaseModel):
    pedido_id: int
    cliente: str
    fecha_creacion: str
    total: float
    items: List[ItemPedidoResponse]

class PedidoUpdate(BaseModel):
    cliente: Optional[str] = None
    items: Optional[List[ItemPedidoCreate]] = None


app = FastAPI(
    title="Sistema de Gestión de Pedidos",
    description="API con Árbol Binario de Búsqueda y Lista Enlazada",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "message": "Sistema de Gestión de Pedidos",
        "productos_en_arbol": arbol_productos.contador,
        "pedidos_en_lista": lista_pedidos.contador
    }


@app.post("/productos", response_model=Producto)
async def crear_producto(producto: ProductoCreate):
    try:
        arbol_productos.insertar(
            producto.producto_id,
            producto.nombre,
            producto.precio,
            producto.stock
        )
        return Producto(**producto.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/productos/{producto_id}", response_model=Producto)
async def obtener_producto(producto_id: int):
    nodo = arbol_productos.buscar(producto_id)
    if nodo is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    return Producto(
        producto_id=nodo.producto_id,
        nombre=nodo.nombre,
        precio=nodo.precio,
        stock=nodo.stock
    )

@app.get("/productos", response_model=List[Producto])
async def listar_productos():
    productos = arbol_productos.listar_todos()
    return [Producto(**producto) for producto in productos]


@app.post("/pedidos", response_model=PedidoResponse)
async def crear_pedido(pedido: PedidoCreate):
    try:
        items_pedido = []
        for item_create in pedido.items:
            nodo_producto = arbol_productos.buscar(item_create.producto_id)
            if nodo_producto is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Producto con ID {item_create.producto_id} no existe"
                )
            
            if nodo_producto.stock < item_create.cantidad:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para producto {item_create.producto_id}"
                )
            
            item_pedido = ItemPedido(
                producto_id=item_create.producto_id,
                cantidad=item_create.cantidad,
                precio_unitario=nodo_producto.precio
            )
            items_pedido.append(item_pedido)
        
        nodo_pedido = lista_pedidos.agregar_pedido(
            pedido.pedido_id,
            pedido.cliente,
            items_pedido
        )
        
        items_response = [
            ItemPedidoResponse(
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                subtotal=item.subtotal
            )
            for item in nodo_pedido.items
        ]
        
        return PedidoResponse(
            pedido_id=nodo_pedido.pedido_id,
            cliente=nodo_pedido.cliente,
            fecha_creacion=nodo_pedido.fecha_creacion.isoformat(),
            total=nodo_pedido.total,
            items=items_response
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/pedidos/{pedido_id}", response_model=PedidoResponse)
async def obtener_pedido(pedido_id: int):
    nodo = lista_pedidos.buscar_pedido(pedido_id)
    if nodo is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    items_response = [
        ItemPedidoResponse(
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            subtotal=item.subtotal
        )
        for item in nodo.items
    ]
    
    return PedidoResponse(
        pedido_id=nodo.pedido_id,
        cliente=nodo.cliente,
        fecha_creacion=nodo.fecha_creacion.isoformat(),
        total=nodo.total,
        items=items_response
    )

@app.put("/pedidos/{pedido_id}", response_model=PedidoResponse)
async def actualizar_pedido(pedido_id: int, pedido_update: PedidoUpdate):
    nodo = lista_pedidos.buscar_pedido(pedido_id)
    if nodo is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    nuevos_items = None
    if pedido_update.items:
        nuevos_items = []
        for item_create in pedido_update.items:
            nodo_producto = arbol_productos.buscar(item_create.producto_id)
            if nodo_producto is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Producto con ID {item_create.producto_id} no existe"
                )
            
            item_pedido = ItemPedido(
                producto_id=item_create.producto_id,
                cantidad=item_create.cantidad,
                precio_unitario=nodo_producto.precio
            )
            nuevos_items.append(item_pedido)
    
    lista_pedidos.actualizar_pedido(
        pedido_id,
        pedido_update.cliente,
        nuevos_items
    )
    
    nodo_actualizado = lista_pedidos.buscar_pedido(pedido_id)
    
    items_response = [
        ItemPedidoResponse(
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            subtotal=item.subtotal
        )
        for item in nodo_actualizado.items
    ]
    
    return PedidoResponse(
        pedido_id=nodo_actualizado.pedido_id,
        cliente=nodo_actualizado.cliente,
        fecha_creacion=nodo_actualizado.fecha_creacion.isoformat(),
        total=nodo_actualizado.total,
        items=items_response
    )

@app.delete("/pedidos/{pedido_id}")
async def eliminar_pedido(pedido_id: int):
    eliminado = lista_pedidos.eliminar_pedido(pedido_id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"mensaje": f"Pedido {pedido_id} eliminado correctamente"}

@app.get("/pedidos", response_model=List[PedidoResponse])
async def listar_pedidos():
    pedidos_dict = lista_pedidos.listar_todos_pedidos()
    
    pedidos_response = []
    for pedido_dict in pedidos_dict:
        items_response = [
            ItemPedidoResponse(**item) for item in pedido_dict["items"]
        ]
        
        pedido_response = PedidoResponse(
            pedido_id=pedido_dict["pedido_id"],
            cliente=pedido_dict["cliente"],
            fecha_creacion=pedido_dict["fecha_creacion"],
            total=pedido_dict["total"],
            items=items_response
        )
        pedidos_response.append(pedido_response)
    
    return pedidos_response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)