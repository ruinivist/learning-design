# Design Patterns

A brief overview of the common ones "they" like to ask

# Creational Patterns

How to create objects

## Factory Pattern

### When?

Tight coupling between the client code and the concrete classes of a particular type.

Case: Client works with Transport of different types (e.g., Car, Bike, Truck) with a common interface and doesn't need to know the specific class it is working with.
If client knows if it's Truck or Car, adding Ship would require change clinet logic.
Violates OCP (Open/Closed Principle) (Should be open for extension but closed for modification). Client is not closed for modification as without this I need to add the if else branching whenever I add a new transport.

### What are the elements?

- **Product Interface**: The contract that the client code works with
- **Concrete Products**: The specific implementations of the different product interface ( of the same subtype )
- **Creator (Abstract Factory)**: The client code logic that works with an abstract product interface.
- **Concrete Creators (Concrete Factories)**: The logic that instantiates the concrete products based on some input or configuration.

Idea is that for the decoupling, there are 2 levels of abstraction, one for the product and one for the client code that works with the product.

### Code

```java
// 1. Product Interface
public interface Transport {
    void deliver();
}

// 2. Concrete Products
public class Truck implements Transport {
    @Override
    public void deliver() {
        System.out.println("Delivering by land in a box.");
    }
}
public class Ship implements Transport {
    @Override
    public void deliver() {
        System.out.println("Delivering by sea in a container.");
    }
}

// 3. abstract creator factory
// client works with abstract product
public abstract class Logistics {
    public abstract Transport createTransport();
    public void planDelivery() {
        Transport transport = createTransport();

        System.out.println("Logistics: Planning delivery...");
        transport.deliver();
    }
}
// 4. concrete creator factories
// no need to define plan delivery again
public class RoadLogistics extends Logistics {
    @Override
    public Transport createTransport() {
        return new Truck();
    }
}
public class SeaLogistics extends Logistics {
    @Override
    public Transport createTransport() {
        return new Ship();
    }
}
```

## Abstract Factory Pattern

### When?

When there are families of classes that share a "variant" and need to be consistent in use.
Eg: if you use ModernTable(), you want to use ModernChair() and ModernSofa() together but tracking it manually is error-prone.

### What are the elements?

Think of this as a 2d grid: vertical are the classes and horizontal are the variants.

- **Abstract Products**: For each vertical class ( product type, not variant ), define an abstract product interface.
- **Concrete Products**: For each variant ( horizontal ), define concrete implementations of the abstract products ( variant x product types implementations ).
- **Abstract Factory**: Maintains classes of abstract products, the client code works direcly with this as an abstraction
- **Concrete Factories**: For each variant, satisty the abstract factory by making concrete products of that same variant.
- **Client**: (optional) you can just jam it into the abstract factory but often client works with the abstract factory as one of the dependencies and not a child of it.

### Code

```java
// 1. Abstract Products: Declare interfaces for a distinct product family
interface Chair {
    method sitOn()
}

interface Sofa {
    method lieOn()
}

// 2. Concrete Products: Implement these interfaces for specific variants
class ModernChair implements Chair { ... }
class VictorianChair implements Chair { ... }

class ModernSofa implements Sofa { ... }
class VictorianSofa implements Sofa { ... }

// 3. Abstract Factory: Declares methods to create EACH product type
interface FurnitureFactory {
    method createChair(): Chair
    method createSofa(): Sofa
}

// 4. Concrete Factories: Implement creation methods for a SPECIFIC variant
class ModernFactory implements FurnitureFactory {
    method createChair(): Chair {
        return new ModernChair()
    }
    method createSofa(): Sofa {
        return new ModernSofa()
    }
}

class VictorianFactory implements FurnitureFactory {
    method createChair(): Chair {
        return new VictorianChair()
    }
    method createSofa(): Sofa {
        return new VictorianSofa()
    }
}

// 5. Client Code
class Application {
    private factory: FurnitureFactory

    constructor(factory: FurnitureFactory) {
        this.factory = factory
    }

    method createFurniture() {
        // The client creates a whole family using one factory instance
        chair = factory.createChair()
        sofa = factory.createSofa()
    }
}
```

## Builder Pattern

### When?

This solves the problem of telescopic constructor which is an anti-pattern.
Case is where a class takes many parameters including optional ones, something like `new House(4, 2, 4, 1, true)`

### What are the elements?

- **Complex Object**: The object that is being constructed which has many parameters.
- **Builder Interface**: Contract that a builder must satisfy
- **Concrete Builder**: Implements the builder interface and provides methods to set each parameter of the complex object ( this and above can be merged, unless you need multiple builders )
- **Director**: (optional) Uses builders to make some predefined configurations of the complex object.

Notice the "gang of four" (2 abstractions + 2 implementations) structure here as well. This is a common occurence and a old OOP pattern. Kind of wasteful often and violates YAGNI.

### Code

```java
// 1. The Product: A complex object
class Car {
    public seats, engine, gps, tripComputer
}

// 2. The Builder Interface: Specifies methods for creating parts of the Product
interface Builder {
    method reset()
    method setSeats(number)
    method setEngine(engine)
    method setGPS(boolean)
}

// 3. Concrete Builder: Implements the steps
class CarBuilder implements Builder {
    private car: Car

    constructor() { this.reset() }

    method reset() { this.car = new Car() }

    method setSeats(number) {
        this.car.seats = number
    }
    method setEngine(engine) {
        this.car.engine = engine
    }
    method setGPS(hasGPS) {
        this.car.gps = hasGPS
    }

    // Returns the result. Note: This is not in the interface usually
    method getResult(): Car {
        return this.car
    }
}
// other builders... perhaps with other optional args

// 4. The Director (Optional): Defines the order of building steps
class Director {
    method makeSportsCar(builder: Builder) {
        builder.reset()
        builder.setSeats(2)
        builder.setEngine(new SportEngine())
        builder.setGPS(true)
    }

    method makeSUV(builder: Builder) {
        builder.reset()
        builder.setSeats(5)
        builder.setEngine(new SUVEngine())
        builder.setGPS(true)
    }
}
```

A modern merged builder

```java
// Modern "Merged" Builder (No Interface)
public class User {
    private final String name;
    private final int age;

    // Private constructor: The User is still immutable
    private User(Builder builder) {
        this.name = builder.name;
        this.age = builder.age;
    }

    // --- 1. The Builder (NON-FLUENT) ---
    public static class Builder {
        // We can make these public for direct access, or private with getters
        public String name;
        public int age;

        public void setName(String name) {
            this.name = name;
        }

        public void setAge(int age) {
            this.age = age;
        }

        public User build() {
            return new User(this);
        }
    }

    // --- 2. The Presets ---

    // This method creates a builder, configures it, and returns the OBJECT
    public static Builder oldBuilder() {
        Builder builder = new Builder();
        builder.setAge(50); // We set the default here
        return builder;
    }

    public static Builder youngBuilder() {
        Builder builder = new Builder();
        builder.setAge(20);
        return builder;
    }
}
```

## Fluent pattern ( subtype of builder )

### When?

Same usecase as builder pattern but with focus on readability of the client code.

### What are the elements?

Same as builder, it's the api that's different.

- changes `setProperty(value)` to `withProperty(value)` returning `this` for chaining.

This ultimately allows for this style of client code:

```java
User user = new User.Builder()
                    .withName("John Doe")
                    .withAge(30)
                    .build();
```

### Example

The above modern example using fluent style

```java
public class User {
    private final String name;
    private final int age;

    // Private constructor so only the Builder can call it
    private User(Builder builder) {
        this.name = builder.name;
        this.age = builder.age;
    }

    // --- 1. The Single "Merged" Builder ---
    public static class Builder {
        private String name;
        private int age;

        // Standard Fluent Setters
        public Builder name(String name) {
            this.name = name;
            return this;
        }

        public Builder age(int age) {
            this.age = age;
            return this;
        }

        public User build() {
            return new User(this);
        }
    }

    // --- 2. The "Presets" (This replaces the need for subclasses) ---

    // Returns a Builder pre-set to age 50
    public static Builder oldBuilder() {
        return new Builder().age(50);
    }

    // Returns a Builder pre-set to age 20
    public static Builder youngBuilder() {
        return new Builder().age(20);
    }
}
```

## Prototype Pattern

### When?

Let's say a class has 100s of configuration parameters, and I just want to use it with one of them changed.
Creating an interface for it and a builder is too much of an overkill. I just want to do a `clone` and change the params.

However, cloning is hard:

- might not have access to private params to do a full deep copy
- a manual clone is tied to that "specific" class so all I know is the interface but not the concrete class, copy is hard.

### What are the elements?

Basically classes need be "clonable" and hence must satisfy the prototype interface.

- **Prototype Interface**: Declares a method for cloning itself.
- **Concrete Prototypes**: Implements the clone method to return a copy of itself.

The implementation is often done via a copy-constructor that takes an existing object of the same class and copies its fields ( including private ones ).

**Prototype registry ( optional )**
The idea is to have a hashmap storing the common prototypes, so that client code can just ask for a clone of a named prototype.

### Example

```java
// 1. The Prototype Interface: Declares the cloning method
interface Prototype {
    method clone(): Prototype
}

// 2. Concrete Prototype: Implements the cloning logic
class Robot implements Prototype {
    private int x, y
    private string type
    public List<string> weapons

    constructor(x, y, type) { ... }

    // A special constructor that takes an existing object of the same class
    // This allows copying private fields safely
    constructor(Robot source) {
        this.x = source.x
        this.y = source.y
        this.type = source.type
        // Deep copy logic would go here (more on this below)
        this.weapons = new List(source.weapons)
    }

    // The clone method calls the special copy-constructor
    method clone(): Prototype {
        return new Robot(this)
    }
}

// 3. Client Code
class Game {
    method spawnEnemies() {
        // Create one "Master" template
        Robot masterRobot = new Robot(0, 0, "Android")
        masterRobot.addWeapon("Laser")

        // Create 50 copies of the master
        // The client DOES NOT know this is a "Robot" class specifically,
        // it just treats it as a "Prototype".
        for (i = 0 to 50) {
            Robot clone = masterRobot.clone()
            list.add(clone)
        }
    }
}
```

## Singleton

### When?

Two main reasons:

- A very common class that is used everywhere and having multiple instances would be wasteful or cause inconsistency.
- To limit the nummber of instances clients can make

### What are the elements?

The aims are basically to have _safe_ global access and ensure there is only one instance. Constructors must return a new instance so can't allow a public constructor.

- **Private Constructor**: Prevents clients from using `new` to create instances.
- **Private static field**: Holds the single instance of the class.
- **Public static accessor method**: To create (if needed) and return the single instance. Usually called the private constructor.

**Optionals**

- **Lazy initialization**: Create when instance is first requested.
- **Thread safety**: the `instance != null` check needs to be thread safe and locked under a mutex if using lazy init.
- **Eager init**: Define on class load, `static instance = new Singleton()` This is thread safe as ran once on class load when the program starts but wastes resources if never used.

**Anti-patterns**

- **Hidden deps**: if a singleton is used, I can't that by looking at the class signature. ( pulling anything from anywhere problem )
- **Testing is hard**: can't mock the args easily as since it's global state, actual state of app ( anything changed in the singleton via other code ) diverges from test state.

Hence modern practice is to use dependency injection instead of singletons.

### Example

```java
class Singleton {
    // 1. A static field that holds the single instance
    private static instance: Singleton

    // 2. The constructor MUST be private to prevent 'new' calls
    private constructor() {
        // Initialization code (e.g., connect to DB)
    }

    // 3. The public static method that controls access
    public static method getInstance(): Singleton {
        // Lazy Loading: If the instance doesn't exist yet, create it.
        if (this.instance == null) {
            this.instance = new Singleton()
        }
        // If it already exists, just return the existing one.
        return this.instance
    }

    public method doBusinessLogic() {
        // ...
    }
}
```

## Object Pool Pattern

### When?

When object instantiation is expensive ( e.g., db connections, threads ) or if just too many objects are needed at once ( e.g., bullets in a game ).

### What are the elements?

- **Pool**: Manages the reusable objects. Keeps track of available and in-use objects (usually a singleton).
- **Reusable Object**: The class of objects being pooled. Must support resetting its state for reuse.
- **Acquire and Release Methods**: Methods in the pool to get an object from the pool and return it back.

### Example

```java
// 1. The Reusable Object
class Connection {
    // Expensive initialization happens here
    constructor() { ... }

    method query(sql) { ... }
}

// 2. The Pool Class
class ConnectionPool {
    private available: List<Connection>
    private inUse: List<Connection>

    method acquire(): Connection {
        if (available.isEmpty()) {
            // Create a new one only if none are free
            connection = new Connection()
        } else {
            // Recycle an existing one
            connection = available.pop()
        }

        inUse.add(connection)
        return connection
    }

    method release(connection: Connection) {
        inUse.remove(connection)

        // Clean the object before putting it back (reset state)
        connection.reset()

        available.add(connection)
    }
}
```

### Generic Pool Example

Since in java we can't do generics with new T(), we need a factory interface to create/reset the objects.

```java
// 1. The Factory Interface: Tells the pool how to create/reset the object
interface PoolableFactory<T> {
    method create(): T
    method reset(item: T) // Optional: clean up object before reuse
}

// 2. The Generic Pool Class
class GenericPool<T> {
    private available: List<T>
    private inUse: List<T>
    private factory: PoolableFactory<T>

    // Constructor takes the factory as an argument
    constructor(factory: PoolableFactory<T>) {
        this.factory = factory
        this.available = new List<T>()
        this.inUse = new List<T>()
    }

    method acquire(): T {
        if (available.isEmpty()) {
            // We use the factory interface to create the specific type
            item = factory.create()
        } else {
            item = available.pop()
        }

        inUse.add(item)
        return item
    }

    method release(item: T) {
        inUse.remove(item)

        // Use factory to reset the state (e.g., set health back to 100)
        factory.reset(item)

        available.add(item)
    }
}
```

## Summary

```
| Pattern   | Idea |
|-----------|------|
| Adapter   | Wraps an incompatible object to make it look like another interface. |
| Bridge    | Separates an object's abstraction (what it is) from its implementation (how it works). |
| Composite | Arranges objects into a tree structure so single items and groups are treated the same. |
| Decorator | Wraps an object recursively to add new behaviors dynamically. |
| Facade    | Provides a single, simplified entry point to a complex system of classes. |
| Flyweight | Shares common parts of state between multiple objects to save RAM. |
| Proxy     | Acts as a substitute to control access (lazy loading, security) to the real object. |
```

# Structural Patterns

How to compose objects and classes into larger structures ( like how they are merged into different structures )

## Adapter

The name comes from the US-Europe power plug adapters that let you plug US devices into European sockets.

### When?

When I have two incompatible interfaces that need to work together. Think of a car running on a railroad track. Usually it's a "glue" to make two incompatible parts of an app work together.
Example is if I had an older charting library that works with XML and so I have all my data sources in XML and now I want to use a new charting library that works with JSON only.

**after-the-fact integration** is the key usecase for adapter. Never a clean state choice.

### What are the elements?

> Remembering: adator adaptee, mentor mentee: ee is the lower one, or is the higher one ( I don't forget this but this doesn't come intuitively to me and I have follow a chain of thought to get this )

- **Target Interface**: The interface that the client code expects to work with.
- **Source Interface**: The current broken interface that needs adapting.
- **Adapter**: Wraps the source interface and implements the target interface, translating calls as needed.

Note that the target is never concrete. Source interface does have concrete implementations ( but not needed for building the adapter, only for actually using it )

### Code

```java
// 1. The Target Interface: This is what the Client code expects to see.
interface MediaPlayer {
    method play(fileType, fileName)
}

// 2. The Adaptee: The useful class with an incompatible interface.
// Notice it has different method names and logic.
class AdvancedAudioPlayer {
    method playVlc(fileName) { ... }
    method playMp4(fileName) { ... }
}

// 3. The Adapter: Wraps the Adaptee to look like the Target.
class MediaAdapter implements MediaPlayer {
    private advancedMusicPlayer: AdvancedAudioPlayer

    constructor(fileType) {
        if (fileType == "vlc")
            this.advancedMusicPlayer = new AdvancedAudioPlayer()
        // ...
    }

    method play(fileType, fileName) {
        // Translate the call from the Standard Interface to the Advanced Interface
        if (fileType == "vlc") {
            this.advancedMusicPlayer.playVlc(fileName)
        } else if (fileType == "mp4") {
            this.advancedMusicPlayer.playMp4(fileName)
        }
    }
}

// 4. Client Code
class AudioPlayer implements MediaPlayer {
    method play(fileType, fileName) {
        // The client simply calls "play". It doesn't know an adapter
        // is doing translation work behind the scenes.
        if (fileType == "mp3") {
            // ... standard logic ...
        } else if (fileType == "vlc" || fileType == "mp4") {
            adapter = new MediaAdapter(fileType)
            adapter.play(fileType, fileName)
        }
    }
}
```

## Bridge Pattern

This is a way of heirarchy flattening ( composition over inheritance ). Idea is **pairing A x B**.

### When?

Let's say I have multiple interfaces ( two for example ) and I want concrete implementations that combine both interfaces. Example: `Shape` and `Color` interfaces.
A crude implementation required cartesian product of classes: `RedCircle`, `BlueCircle`, `RedSquare`, `BlueSquare` etc.

What can instead be done is that the `Shape` interface works with `Color` interface via composition ( as arg ) instead of inheritance ( extending ).

### What are the elements?

- **Abstract type A and B**: Two separate hierarchies that need to be combined (initial state)
- **Refined Abstraction A**: The first hierarchy ( type A ) that contains a reference to the second hierarchy ( type B )
- **Concrete Implementor B**: The second hierarchy ( type B ) that provides concrete implementations.
- **Client**: Works with the first hierarchy ( type A ) and uses the second hierarchy ( type B ) via composition.

This is different from just multi-level inheritance as it combines two separate hierarchies via composition instead of extending a level to the current hierarchy.

> Brige is one of the intuitive and surprisingly common patterns. It's not like a "named" thing as the idea of composition over inheritance is a general principle. If you forget what composition over inheritance is, think of how react elements wrap other elements instead of extending them.

What is the order of A and B? Do I compose Shapes or Color? The idea is that A ( higher ) is the one that the client code direcly works with. So if client uses Shapes then you move Color to be inside Shape.

### Example

```java
// 1. The Implementation Interface (The "Color" dimension)
interface Color {
    method fill()
}

// 2. Concrete Implementations
class Red implements Color {
    method fill() { return "Red" }
}

class Blue implements Color {
    method fill() { return "Blue" }
}

// 3. The Abstraction (The "Shape" dimension)
// It holds a reference (bridge) to the Implementation
abstract class Shape {
    protected color: Color

    constructor(color: Color) {
        this.color = color
    }

    abstract method draw()
}

// 4. Refined Abstractions
class Circle extends Shape {
    constructor(color: Color) {
        super(color)
    }

    method draw() {
        // The Shape logic (drawing circle) is combined with
        // the Implementation logic (filling color) via the bridge.
        print("Drawing Circle in " + color.fill())
    }
}

class Square extends Shape {
    constructor(color: Color) {
        super(color)
    }

    method draw() {
        print("Drawing Square in " + color.fill())
    }
}
```

## Composite

### When?

When you have a tree-like structure of objects and want to run a particular behaviour recursively. Example is a file system. You would want both types of nodes to satisy a common interface that has a `getSize()` method. For a file, it's just the file size. For a directory, it's the sum of sizes of all its children ( files and sub-directories ).

### What are the elements?

- **Tree structure**: Class A must have children of type A or others ( recursive composition )
- **Component Interface**: The common interface that both leaf and composite nodes implement.
- **Leaf**: The end nodes that don't have children.
- **Composite**: The nodes that have children and implement the component interface by delegating to their children and aggregating results.

This way the concerns are separated. Leaf nodes handle their own logic, while composite nodes handle the recursive aggregation.

> This too feels like a general principle of recursive composition that's often used even if you don't know the name explicitly.

### Example

```java
// 1. The Component: The common interface for everything in the tree.
interface FileSystemNode {
    method getSize(): int
}

// 2. The Leaf: A basic element (no children).
class File implements FileSystemNode {
    private size: int

    constructor(size) { this.size = size }

    method getSize(): int {
        return this.size
    }
}

// 3. The Composite: A container that holds Leaves or other Composites.
class Directory implements FileSystemNode {
    private children: List<FileSystemNode> = []

    method add(node: FileSystemNode) {
        children.add(node)
    }

    // The Magic: It delegates the work to its children recursively.
    method getSize(): int {
        total = 0
        for (node in children) {
            total += node.getSize()
        }
        return total
    }
}
```

## Decorator

The idea is **stacking A + B + C** at **runtime** instead of compile time ( inheritance ).

### When?

Think of it as a Person class, wearing different clothes ( Hat, Shirt, Pants ) at different times. Instead of making a new subclass for each combination ( e.g., PersonWithHatAndShirt ), we can dynamically add clothes as needed. This looks related to Bridge as you can just do `PersonWithClothes` but what if there is no common abstraction for clothes. And it makes more sense to add Clothes on top of Person instead of making Person aware of Clothes ( Clothes modify the Person behavior ).

Another key distinction over bridge is that you can have multiple decorators ( contract with RedAndGreen ) which is not a possibility with bridge example earlier.

Also if it's subclass that's not in your control and has `final` that you can't extend, decorator is the way.

Note that the decorators must have some common interface that allows for composition and usually A + B being same as B + A.

### What are the elements?

- **Base interface**: The decorator implements this interface so that wrapping can be chained.
- **Base Decorator Interface**: The logic common to decorators.
- **Concrete Decorators**: Implements the decorator interface and adds new behavior before/after delegating to the base object. They usually call some `super` method to get the base behavior and then add their own logic.

> This is one of the non-trivial patterns to me.

### Example

```java
// 1. The Component Interface
interface Coffee {
    method getCost(): double
    method getDescription(): string
}

// 2. Concrete Component (The Base Object)
class SimpleCoffee implements Coffee {
    method getCost() { return 5.0 }
    method getDescription() { return "Coffee" }
}

// 3. The Base Decorator
// It implements the interface AND holds a reference to a component
abstract class CoffeeDecorator implements Coffee {
    protected wrappedCoffee: Coffee

    constructor(coffee: Coffee) {
        this.wrappedCoffee = coffee
    }

    // Default behavior: just delegate to the wrapped object
    method getCost() { return wrappedCoffee.getCost() }
    method getDescription() { return wrappedCoffee.getDescription() }
}

// 4. Concrete Decorators (The Add-ons)
class Milk extends CoffeeDecorator {
    constructor(coffee: Coffee) { super(coffee) }

    method getCost() {
        // Add own cost + cost of whatever is inside
        return super.getCost() + 2.0
    }

    method getDescription() {
        return super.getDescription() + ", Milk"
    }
}

class Sugar extends CoffeeDecorator {
    constructor(coffee: Coffee) { super(coffee) }

    method getCost() { return super.getCost() + 1.0 }
    method getDescription() { return super.getDescription() + ", Sugar" }
}

// Usage
Coffee myDrink = new SimpleCoffee()          // Cost: 5
myDrink = new Milk(myDrink)                  // Cost: 7 (Wrapped in Milk)
myDrink = new Sugar(myDrink)                 // Cost: 8 (Wrapped in Sugar)
```

## Facade Pattern

### When?

Aggregating complex subsystems into a simple interface. Say you have a lot of classes that need to work together in a definite order to perform some common high-level task. Instead of making the client code deal with all the complexity, you provide a simple facade class that wraps the complex logic.

The idea is simply wrapping of an abstraction. Pretty common.

### What are the elements?

- No new functionality is added. It just simplifies the interface.
- You have a wrapper class that holds references to the complex subsystems and provides simple methods that internally call the complex logic in the right order.

### Example

```java
// 1. The Complex Subsystem (The scary library classes)
class VideoFile { ... }
class OggCompressionCodec { ... }
class MPEG4CompressionCodec { ... }
class CodecFactory { ... }
class BitrateReader { ... }
class AudioMixer { ... }

// 2. The Facade (The friendly face)
class VideoConverterFacade {

    // The client only needs to call this ONE simple method
    method convertVideo(fileName, format): File {
        file = new VideoFile(fileName)

        // The Facade handles the dirty work of logic and object creation
        sourceCodec = CodecFactory.extract(file)
        if (format == "mp4") {
            destCodec = new MPEG4CompressionCodec()
        } else {
            destCodec = new OggCompressionCodec()
        }

        buffer = BitrateReader.read(fileName, sourceCodec)
        result = AudioMixer.fix(buffer)

        return new File(result)
    }
}

// 3. Client Code
class Application {
    method main() {
        // Without Facade: 20 lines of complex setup code.
        // With Facade: 1 clean line.

        converter = new VideoConverterFacade()
        mp4 = converter.convertVideo("funny_cat.ogg", "mp4")
    }
}
```

## Flyweight Pattern

### When?

For fixing OOM/resource contraints when a large number of objects share the same data. It's like a `scoped singleton` where within a scope you have only one instance of the resource-heavy objects.

### What are the elements?

- The organisation is a combination of object pool and singletons.
- **Flyweight Interface**: The common interface for the flyweight objects. This holds the intrinsic state ( shared data ).
- **Concrete Flyweight**: Implements the flyweight interface and holds the intrinsic state.
- **Flyweight Factory**: Manages the pool of flyweight objects. It checks if a flyweight with the required intrinsic state already exists; if so, it returns that instance; otherwise, it creates a new one.
- **Extrinsic State**: Composition into a super class that holds extrinsic state ( unique data ) and a shared reference to the flyweight.

### Example

The interface and concrete are merged here ( no interface needed )

```java
// 1. The Flyweight (Intrinsic State)
// This class holds the heavy data. We only make ONE of these per tree type.
class TreeType {
    private name: String
    private color: String
    private texture: BigHeavyTexture // 5MB

    constructor(name, color, texture) { ... }

    // The operation needs the extrinsic state (x, y) passed in as arguments
    method draw(canvas, x, y) {
        // Draw this texture at the specific x, y
    }
}

// 2. The Factory (Manages the Flyweights)
class TreeFactory {
    static treeTypes = Map<String, TreeType>()

    static method getTreeType(name, color, texture) {
        // If we already made this type of tree, return the existing one.
        // If not, create it and cache it.
        result = treeTypes.find(name)
        if (result == null) {
            result = new TreeType(name, color, texture)
            treeTypes.add(name, result)
        }
        return result
    }
}

// 3. The Context (Extrinsic State)
// This is the lightweight object. It only holds coordinates and a reference.
class Tree {
    private x: int
    private y: int
    private type: TreeType // Reference to the heavy object

    constructor(x, y, type) {
        this.x = x
        this.y = y
        this.type = type
    }

    method draw(canvas) {
        // Delegate the drawing to the flyweight, passing the unique data
        type.draw(canvas, this.x, this.y)
    }
}

// 4. Client Code (The Forest)
class Forest {
    method plantTrees() {
        // We create 1,000,000 trees...
        for (i = 0 to 1000000) {
            // ...but we only ever create 2 "TreeType" objects in memory!
            type = TreeFactory.getTreeType("Oak", "Green", "OakTexture.png")
            tree = new Tree(randomX, randomY, type)
        }
    }
}
```

## Proxy

### When?

When you want to access control another object or add pre/post logic around it's methods. You cannot always implement in the base class itself ( e.g., final classes or 3rd party libraries, separation of concerns ).

The idea is simple and often used in practice without knowing the specfic name.

### What are the elements?

- **Real Interface**: The common interface that both the real object and the proxy implement.
- **Real Subject**: The actual object that does the real work.
- **Proxy Interface**: Implements the real interface and holds a reference to the real subject. It adds pre/post logic around calls to the real subject.

### Example

```java
// 1. The Subject Interface
// Both the Real object and the Proxy implement this.
interface ThirdPartyYouTubeLib {
    method listVideos()
    method downloadVideo(id)
}

// 2. The Real Subject
// The actual heavy lifting class.
class RealYouTubeService implements ThirdPartyYouTubeLib {
    method listVideos() { ... }
    method downloadVideo(id) {
        // Connects to server, downloads byte stream... (Slow & Expensive)
    }
}

// 3. The Proxy
// It intercepts calls to the real object.
class CachedYouTubeProxy implements ThirdPartyYouTubeLib {
    private service: RealYouTubeService
    private listCache: List
    private videoCache: Map<id, Video>

    method listVideos() {
        if (listCache == null) {
            // Lazy Initialization: Create the real service only when needed
            if (service == null) { service = new RealYouTubeService() }
            listCache = service.listVideos()
        }
        return listCache
    }

    method downloadVideo(id) {
        if (!videoCache.containsKey(id)) {
             if (service == null) { service = new RealYouTubeService() }
             videoCache.put(id, service.downloadVideo(id))
        }
        return videoCache.get(id)
    }
}
```

## Summary

| Pattern   | Description                                   |
| --------- | --------------------------------------------- |
| Adapter   | Makes incompatible interfaces work together.  |
| Bridge    | Separates A x B dimensions                    |
| Composite | Trees of objects (Folders/Files).             |
| Decorator | Adds responsibilities dynamically (Wrappers). |
| Facade    | Simplified interface to a complex system.     |
| Flyweight | Shares memory for massive numbers of objects. |
| Proxy     | Controls access to an object.                 |

# Behavioral Patterns

How the logic ( instead of structure is composed ). Think responsiblity and delegation. Less focused on creating classes and more on how they interact.

## Chain of Responsibility

This is complex and several varations are possible. Idea is to follow Open/Closed principle by having a chain of handlers that can process a request ( you add new handlers than modifying existing code ).

### Variations

#### Structural ( how the chain is built )

- **Linked List**: Each handler has a reference to the next handler. Very flexible but needs wiring.
- **Method Override**: Each handler overrides the method to decide whether to handle or call super. Flows from leaf to top. Either leaf can handle or call super's handler ( think handling of hover events in a UI tree ). Inflexible as chain is fixed by inheritance.
- **Manager Class**: A separate class holds the chain and manages passing requests along. Handlers don't know about each other. More decoupled but need one more class.

#### Behavioral ( how requests flow )

- **Short-circuiting**: Only one handler processes the request and stops the chain.
- **Pass through**: Each handler can process/noop and then pass to next. Useful for logging, validation etc.
- **Bidirectional**: Requests can flow both ways in the chain. Example: DOM event capturing/bubbling.

### When?

When there are different requsts and the sequence for handling is dynamic based on the request. The pattern's idea is to avoid ifs and keep loose coupling.
The most common example is the http request and middleware chain.

### What are the elements?

- **Handler Interface**: Common interface for all handlers in the chain ( basically an interface that makes it a handler ).
- **Successor Link/Overrides**: This can be actual via a reference of implicit via override of a method.

### Example

This is a pass through handler using linked list.

```java
// 1. The Interface
Interface Middleware {
    Method setNext(Middleware next)
    Method handle(HttpRequest request)
}

// 2. The Pass-Through Handler (e.g., Logger)
// It does work, then passes the ball.
Class LoggerMiddleware implements Middleware {
    Field next: Middleware

    Method handle(request) {
        // A. Pre-processing (Going down the chain)
        print("Log: Request started for " + request.url)

        // B. PASS-THROUGH: Call the next link
        HttpResponse response = null
        if (this.next is distinct) {
            response = this.next.handle(request)
        }

        // C. Post-processing (Coming back up the chain)
        print("Log: Request finished with status " + response.status)

        return response
    }
}

// 3. The Pass-Through with Logic (e.g., Auth)
// It only passes through if the check passes.
Class AuthMiddleware implements Middleware {
    Field next: Middleware

    Method handle(request) {
        if (request.user == null) {
            // STOP THE CHAIN: Do NOT call next
            return new HttpResponse(401, "Unauthorized")
        }

        // Pass-through
        return this.next.handle(request)
    }
}

// 4. Client Usage
// Logger -> Auth -> (Application Logic)
middleware = new LoggerMiddleware()
middleware.setNext(new AuthMiddleware())

middleware.handle(incomingRequest)
```

DOM two-way bubbling

```java
// 1. Base Component (The Node)
Abstract Class Component {
    Field parent: Component

    // The event handling logic
    Method handleEvent(event) {
        // Step A: Check if *this* component has a listener for this event
        if (this.hasListener(event.type)) {
             this.executeListener(event)

             // Option: Stop bubbling if the listener calls stopPropagation()
             if (event.isPropagationStopped) {
                 return
             }
        }

        // Step B: Bubble up!
        // If I didn't stop it, pass it to my parent.
        if (this.parent exists) {
            this.parent.handleEvent(event)
        }
    }
}

// 2. Concrete Element
Class Button inherits Component {
    // inherits handleEvent logic automatically
}

// 3. Concrete Container
Class Div inherits Component {
    // inherits handleEvent logic automatically
}
```

Another way is where each handler overrides the method (if needed) to show custom logic else just uses the parent's logic.

> In general think of CoR aas the "next" based delegation pattern.

## Command Pattern

### When?

A command is an action. The idea is to separate the "action" and the "invoker" of the action. So ui buttons can be decoupled from the actual logic they trigger. Think of it as like having a separate function for each of the actions. Except, here we encapsulate the action as an object and this allows us to easily queue, log, undo/redo the actions and add more behavior to the actions.

If these commands are not executed immediately, you can have an event loop of sorts as well, where the invoker just queues commands and a separate loop executes them.

### What are the elements?

- **Command Interface**: Declares a method for executing the command.
- **Receiver**: The object that knows how to perform the actual action.
- **Concrete Command**: Implements the command interface and defines the binding between a receiver and an action. Usually holds a reference to the receiver and calls its methods.
- **Invoker**: UI layer, knows nothing of the command's logic except "what command" ( if wired to a button, based on args like `Button(action: command)`, same as `onclick` )

### Example

```java
// 1. The Command Interface
// Declares the execution method
Interface Command {
    Method execute()
    Method undo() // Optional, but common
}

// 2. The Receiver
// The business logic layer. It knows HOW to do the work.
Class Light {
    Method turnOn() { print("Light is ON") }
    Method turnOff() { print("Light is OFF") }
}

// 3. Concrete Commands
// Wraps the Receiver and binds a specific action to it.
Class LightOnCommand implements Command {
    Field light: Light

    Constructor(light) { this.light = light }

    Method execute() {
        this.light.turnOn()
    }

    Method undo() {
        this.light.turnOff()
    }
}

Class LightOffCommand implements Command {
    Field light: Light
    Constructor(light) { this.light = light }
    Method execute() { this.light.turnOff() }
    Method undo() { this.light.turnOn() }
}

// 4. The Invoker
// The "Remote Control" or "Button". It knows nothing about the Light.
Class RemoteControl {
    Field command: Command

    Method setCommand(command) {
        this.command = command
    }

    Method pressButton() {
        // Delegates work to the command object
        if (this.command exists) {
            this.command.execute()
        }
    }
}

// 5. Client Code
Method main() {
    // A. Setup Receiver
    livingRoomLight = new Light()

    // B. Create Command (Parameterize the object)
    turnOn = new LightOnCommand(livingRoomLight)

    // C. Setup Invoker
    remote = new RemoteControl()

    // D. Execute
    remote.setCommand(turnOn)
    remote.pressButton() // Output: "Light is ON"
}
```

A queue based approach

```java
// 1. The Command Interface
Interface Command {
    Method execute()
}

// 2. Concrete Command (Self-contained unit of work)
// It captures ALL the data needed to run the task later.
Class SendEmailCommand implements Command {
    Field emailAddress: String
    Field messageBody: String
    Field service: EmailService

    // Constructor: Store the data for later use
    Constructor(service, email, message) {
        this.service = service
        this.emailAddress = email
        this.messageBody = message
    }

    Method execute() {
        print("Sending email to " + this.emailAddress + "...")
        this.service.send(this.emailAddress, this.messageBody)
    }
}

// 3. The Invoker (The Queue Manager)
// It doesn't know WHAT the tasks are, only that they are commands.
Class JobQueue {
    Field queue: List<Command>

    Method addJob(command) {
        this.queue.add(command)
        print("Job added. Queue size: " + this.queue.size())
    }

    // This method is called later (e.g., by a background thread or timer)
    Method processPendingJobs() {
        for (command in this.queue) {
            command.execute()
            // Optional: Remove from queue after success
        }
        this.queue.clear()
    }
}

// 4. Client Code
Method main() {
    // Setup
    queue = new JobQueue()
    emailService = new EmailService()

    // A. Create Requests (But don't run them yet)
    cmd1 = new SendEmailCommand(emailService, "boss@corp.com", "Report attached")
    cmd2 = new SendEmailCommand(emailService, "client@gmail.com", "Welcome!")

    // B. "Store" them for later
    queue.addJob(cmd1)
    queue.addJob(cmd2)

    print("--- User continues doing other work ---")

    // C. Delayed Execution
    // Imagine this happens 10 minutes later or on a different thread
    print("--- Processing Background Jobs ---")
    queue.processPendingJobs()
}
```

## Iterator

This one is easy. Often you want to write code that works with collections but is generic enough to work with any collection type ( array, linked list, tree etc. ). So the task of building the iterator and the next/hasNext logic is moved to the collection itself, and the client code just uses the iterator interface.

### What are the elements?

- **Iterator Interface**: that the individual iterator has to satisfy
- **Iterable Interface**: that the collection has to satisfy
- **Concrete Collection**: of both above

### Example

```java
// 1. The Iterator Interface
// The standard "remote control" for traversal
Interface Iterator {
    Method hasNext()
    Method next()
}

// 2. The Iterable Interface
// Declares that an object can provide an iterator
Interface IterableCollection {
    Method createIterator() -> Iterator
}

// 3. Concrete Collection
Class BookList implements IterableCollection {
    Field books: Array

    Method createIterator() {
        return new BookIterator(this)
    }
}

// 4. Concrete Iterator
// Keeps track of WHERE we are in the traversal
Class BookIterator implements Iterator {
    Field collection: BookList
    Field currentIndex: int = 0

    Method hasNext() {
        return currentIndex < collection.books.length
    }

    Method next() {
        return collection.books[currentIndex++]
    }
}

// 5. Client Code
Method main() {
    library = new BookList()

    // Client doesn't know if it's an Array or Linked List
    iterator = library.createIterator()

    while (iterator.hasNext()) {
        print(iterator.next())
    }
}
```

## Mediator Pattern

### When?

When you have a lot of classes that interact with each other directly, leading to tight coupling and complex dependencies. Could be like if component A has this and component B has that, then component C does this and so on. The idea is that instead of each component talking to each other directly, they talk to a central mediator that handles the communication. This reduces dependencies and makes it easier to change or add components without affecting others.

Think of this as a more advanced version of "global state"

> Think of conversion from p2p to centralised server model.

### What are the elements?

- **Star Topology**: So that each component only knows about the mediator, not other components.
- **Mediator Interface**: Declares methods for communication between components.
- **Concrete Mediator**: Implements the mediator interface and coordinates communication between components.
- **Child Components**: The individual components that interact through the mediator ( usually have a reference to the mediator and call notify methods on it ).

### Example

```java
// 1. The Mediator Interface
// Defines how components communicate with the hub
Interface Mediator {
    Method notify(sender: Component, event: String)
}

// 2. The Base Component (Colleague)
// Components know about the Mediator, but NOT about other components.
Abstract Class Component {
    Protected Field mediator: Mediator

    Method setMediator(mediator) {
        this.mediator = mediator
    }
}

// 3. Concrete Components
// They just report "what happened" to the mediator.
Class Checkbox inherits Component {
    Method check() {
        // ... logic to check the box ...
        // Notify the hub: "I changed!"
        this.mediator.notify(this, "check")
    }
}

Class Textbox inherits Component {
    Method enable() { /* ... */ }
    Method disable() { /* ... */ }
}

Class Button inherits Component {
    Method click() {
        this.mediator.notify(this, "click")
    }
}

// 4. Concrete Mediator (The Hub)
// Contains the business logic of HOW components interact.
Class AuthenticationDialog implements Mediator {
    Field chkShowPassword: Checkbox
    Field txtPassword: Textbox
    Field btnLogin: Button

    // Wiring code
    Constructor(chk, txt, btn) {
        this.chkShowPassword = chk
        this.chkShowPassword.setMediator(this)

        this.txtPassword = txt
        this.txtPassword.setMediator(this)

        this.btnLogin = btn
        this.btnLogin.setMediator(this)
    }

    // Centralized Logic
    Method notify(sender, event) {
        if (sender == chkShowPassword && event == "check") {
            // Logic: Toggle visibility
            this.txtPassword.toggleVisibility()
        }

        if (sender == btnLogin && event == "click") {
            // Logic: Validate inputs
            if (this.txtPassword.isEmpty()) {
                print("Error: Password missing")
            }
        }
    }
}

// 5. Client Code
Method main() {
    chk = new Checkbox()
    txt = new Textbox()
    btn = new Button()

    // The mediator wires them up and manages the logic
    dialog = new AuthenticationDialog(chk, txt, btn)

    // Trigger
    chk.check()
    // Flow: Checkbox -> Mediator -> Textbox
}
```

## Memento Pattern

### When?

the "undo" feature ( and anything that can be translated as a similar action ). Undo is hard as new class won't have access to the private fields and even if it did, it makes a tight coupling ( any change in state class needs to be reflected in whatever manages the copies ).

### What are the elements?

The idea is for the state ( originator ) class to create it's own snapshots ( mementos ) and hand them off to a caretakes who never peeks inside the mementos

- **Originator**: The object whose state needs to be saved/restored. It creates mementos.
- **Memento**: The snapshot object that holds the state of the originator. It should be immutable to prevent external modification.
- **Caretaker**: Manages the mementos. It requests mementos from the originator and restores state when needed.

### Example

No just immutable but invisible by external classes, to anything outside the concrete mementor doesn't exist at all.

```java
// 1. The Marker Interface
// This is what the outside world (Caretaker) sees.
// It effectively says: "I am a saved state, but I won't tell you what's inside."
interface Memento {
    // Optional: Metadata methods are okay (e.g., date, name)
    // But NO state getters.
    String getName();
}

// 2. The Originator
// The class that has the state we want to save.
class TextEditor {
    private String content;
    private int cursorPosition;

    public void setContent(String content) {
        this.content = content;
    }

    // --- SAVING ---
    public Memento save() {
        // Create a snapshot. We pass 'this.content' to copy the data (immutability).
        return new EditorMemento(this.content, this.cursorPosition);
    }

    // --- RESTORING ---
    public void restore(Memento m) {
        // Cast the generic interface back to the specific inner class.
        // This is safe because we know WE created it.
        if (!(m instanceof EditorMemento)) {
            throw new IllegalArgumentException("Unknown memento class");
        }

        EditorMemento memento = (EditorMemento) m;
        this.content = memento.savedContent;
        this.cursorPosition = memento.savedCursor;
    }

    // 3. The Concrete Memento (Private Inner Class)
    // PRIVATE: No one outside TextEditor can see this class or its fields.
    private static class EditorMemento implements Memento {
        private final String savedContent;
        private final int savedCursor;

        // Constructor is private-ish (accessible to outer class)
        private EditorMemento(String content, int cursor) {
            this.savedContent = content;
            this.savedCursor = cursor;
        }

        @Override
        public String getName() {
            return "Snapshot at " + java.time.LocalDateTime.now();
        }
    }
}

// 4. The Caretaker
// Keeps the mementos safe.
class History {
    private final Stack<Memento> historyStack = new Stack<>();
    private final TextEditor editor;

    public History(TextEditor editor) {
        this.editor = editor;
    }

    public void backup() {
        this.historyStack.push(editor.save());
    }

    public void undo() {
        if (!historyStack.isEmpty()) {
            // Pop the opaque Memento object
            Memento memento = historyStack.pop();
            // Hand it back to the editor to unlock it
            editor.restore(memento);
        }
    }
}

// 5. Client Usage
class Application {
    public static void main(String[] args) {
        TextEditor editor = new TextEditor();
        History history = new History(editor);

        editor.setContent("Version 1");
        history.backup(); // Save

        editor.setContent("Version 2");
        history.backup(); // Save

        editor.setContent("Version 3 (Mistake)");

        history.undo(); // Back to Version 2

        // Note: historyStack.peek().savedContent is IMPOSSIBLE here.
        // Compilation error: "savedContent has private access"
    }
}
```

## Observer

A very common and useful pattern. It's the idea of event driven programming where separate components and subscribe to events and act on them.

### When?

The idea is that for any central source and it's many dependents ( one to many ), you want to make the dependendts loosely coupled. Example is a news feed that sends emails and updates ui. Both email and ui update should not poll constantly ( pull is wasteful, push instead ), neither should the news feed do something like `email.send` or `ui.update` ( tight coupling ).

Idea is instead services can subscribe to events and get notified when something happens.

### What are the elements?

- **Observer interface**: This is what news feed above knows and notifies and what decouples the different other components.
- **Concrete Observers**: The actual components that implement the observer interface and send it off to the news feed.
- **Publisher/Subject**: Can have an interface and concrete to make it cleaner ( like `NewsFeed implement Subscribable` ). It holds a list of observers and notifies them on events.

There are two models of this - push and pull.
If the subject pushes data to observers about what changed, it's push model.
If the subject just notifies "something changed" and sends a `this` pointer to the observers and it is the observer's job to pull the data it needs, it's pull model.

### Example

```java
// 1. The Observer Interface (The Subscriber)
// All listeners must implement this.
Interface Observer {
    Method update(data)
}

// 2. The Subject Interface (The Publisher)
// Manages the list of subscribers.
Class Subject {
    Field observers: List<Observer>

    Method attach(observer) {
        this.observers.add(observer)
    }

    Method detach(observer) {
        this.observers.remove(observer)
    }

    // The "Broadcast" method
    Method notify(data) {
        for (observer in this.observers) {
            observer.update(data)
        }
    }
}

// 3. Concrete Subject
// The real business logic.
Class YouTubeChannel inherits Subject {
    Method uploadVideo(title) {
        print("Uploading: " + title)
        // Something happened! Tell everyone.
        this.notify(title)
    }
}

// 4. Concrete Observers
// They react to the news.
Class User inherits Observer {
    Field name: String

    Method update(videoTitle) {
        print(this.name + ": New notification! " + videoTitle)
    }
}

Class Analytics inherits Observer {
    Method update(videoTitle) {
        print("Analytics: Incrementing upload count for " + videoTitle)
    }
}

// 5. Client Code
Method main() {
    channel = new YouTubeChannel()

    alice = new User("Alice")
    bob = new User("Bob")
    stats = new Analytics()

    // Alice and stats subscribe. Bob doesn't.
    channel.attach(alice)
    channel.attach(stats)

    channel.uploadVideo("Design Patterns 101")
    // Output:
    // Alice: New notification! Design Patterns 101
    // Analytics: Incrementing upload count for Design Patterns 101
}
```

## State Pattern

Closely related to finite state machines except OOP.

### When?

When the behavior depends heavily on what "state" the object is in. Such classes typically would have if and switch in every logic method to modify behavior. Idea is to delegate the behavior to individual state classes ( which isn't too much of a geniuse idea ).

### What are the elements?

- **State Interface**: Declares methods/members that all concrete states must have.
- **Context**: The main class that has a reference to the current state and delegates behavior to it.
- **Concrete States**: Implements the state interface and defines behavior for a specific state. These usually take in a reference to the context to allow state transitions ( cyclic reference needed here ).

### Example

Not really useful given just two states in the example next but shows the idea.

```java
// 1. The Interface
Interface State {
    Method clickPlay()
}

// 2. The Context (The Player)
// It delegates the "click" action to whatever state is currently active.
Class AudioPlayer {
    Field state: State

    Constructor() { this.state = new StoppedState(this) }

    Method changeState(newState) { this.state = newState }

    Method clickPlay() {
        this.state.clickPlay()
    }
}

// 3. Concrete State: Stopped
// Logic: If stopped, clicking play STARTS the music.
Class StoppedState implements State {
    Field player: AudioPlayer
    Constructor(p) { this.player = p }

    Method clickPlay() {
        print("Starting music...")
        // Transition: Stopped -> Playing
        this.player.changeState(new PlayingState(this.player))
    }
}

// 4. Concrete State: Playing
// Logic: If playing, clicking play PAUSES the music.
Class PlayingState implements State {
    Field player: AudioPlayer
    Constructor(p) { this.player = p }

    Method clickPlay() {
        print("Pausing music...")
        // Transition: Playing -> Paused
        this.player.changeState(new PausedState(this.player))
    }
}

// 5. Client Code
player = new AudioPlayer()

player.clickPlay() // Output: "Starting music..." (State switches to Playing)
player.clickPlay() // Output: "Pausing music..."  (State switches to Paused)
```

## Strategy

### When?

Family of algorithms that perform the same task ( hence swappable ) but in different ways ( logic differs, like sorting algos ). The idea is to encapsulate each algorithm in its own class and make them interchangeable
within the context that uses them.

This is dynamic polymorphism via composition rather than static polymorphism via inheritance ( template method ).

### What are the elements?

- **Strategy Interface**: Declares a common interface for all supported algorithms.
- **Concrete Strategies**: Implements the strategy interface with specific algorithms.
- **Context** : Maintains a reference to a strategy object and delegates the algorithm execution to it. Has setters to change strategy at runtime.

### Example

```java
// 1. The Strategy Interface
// Defines the common action for all algorithms.
Interface RouteStrategy {
    Method buildRoute(A, B)
}

// 2. Concrete Strategies
// Different implementations of the same task.
Class RoadStrategy implements RouteStrategy {
    Method buildRoute(A, B) {
        return "Calculated route for CAR: 15 mins"
    }
}

Class WalkingStrategy implements RouteStrategy {
    Method buildRoute(A, B) {
        return "Calculated route for WALKING: 40 mins via Park"
    }
}

// 3. The Context
// The main app. It doesn't care HOW the route is built, just that it gets done.
Class NavigationApp {
    Field strategy: RouteStrategy

    Method setStrategy(strategy) {
        this.strategy = strategy
    }

    Method buildRoute(A, B) {
        // Delegate the work to the strategy
        return this.strategy.buildRoute(A, B)
    }
}

// 4. Client Code
Method main() {
    app = new NavigationApp()

    // Scenario 1: User is driving
    // The Client explicitly CHOOSES the strategy
    app.setStrategy(new RoadStrategy())
    print(app.buildRoute("Home", "Work"))

    // Scenario 2: User decides to walk
    // We swap the algorithm at runtime
    app.setStrategy(new WalkingStrategy())
    print(app.buildRoute("Home", "Work"))
}
```

## Template Method

It's brand new name for what is just inheritance and method overriding.

### When?

You have a similar problem as strategy where bulk of the logic remains same except some methods that need to change. Example, a data processing class that has read, load, save, parse etc but only parse needs to change based on the data format ( csv, json, xml etc ).

### What are the elements?

- **Abstract Class**: Defines the template and the common logic.
- **Concrete Subclasses**: Override specific steps of the algorithm.

### Example

```java
// 1. The Abstract Base Class
// Defines the "Skeleton" of the algorithm.
Abstract Class DataMiner {

    // The "Template Method"
    // It defines the sequence of steps.
    // FINAL: Subclasses cannot change the order of execution.
    Final Method mine(path) {
        file = this.openFile(path)     // Standard step
        raw = this.extractData(file)   // Abstract step (Varies)
        data = this.parseData(raw)     // Abstract step (Varies)
        this.analyze(data)             // Standard step
        this.sendReport()              // Hook (Optional)
        this.closeFile(file)           // Standard step
    }

    // Standard Step: Shared by all subclasses
    Method openFile(path) {
        print("Opening file at " + path)
    }

    Method closeFile(file) {
        print("Closing file")
    }

    Method analyze(data) {
        print("Analyzing generic data...")
    }

    // Abstract Step: Subclasses MUST implement this
    Abstract Method extractData(file)
    Abstract Method parseData(raw)

    // Hook: Subclasses CAN override this, but don't have to.
    // It has a default (often empty) implementation.
    Method sendReport() {
        // Default: Do nothing
    }
}

// 2. Concrete Class: PDF
Class PDFMiner inherits DataMiner {
    Method extractData(file) {
        return "Raw PDF Bytes"
    }

    Method parseData(raw) {
        return "Parsed text from PDF XML"
    }
}

// 3. Concrete Class: CSV
Class CSVMiner inherits DataMiner {
    Method extractData(file) {
        return "Raw CSV String"
    }

    Method parseData(raw) {
        return "Parsed rows and columns"
    }

    // Overriding the Hook
    Method sendReport() {
        print("Sending specific CSV Email Report...")
    }
}

// 4. Client Code
Method main() {
    // The client works with the abstract type, but calls the template method.
    miner = new PDFMiner()
    miner.mine("document.pdf")
    // Flow:
    // 1. DataMiner.openFile()
    // 2. PDFMiner.extractData()
    // 3. PDFMiner.parseData()
    // 4. DataMiner.analyze()
    // 5. DataMiner.closeFile()
}
```

## Visitor Pattern

This is a good one. Double dispatch.

### When?

When there's a complex object ( tree or some other composite ) and some behaviour needs to be defined on nodes. Now you don't want to modify that same one function on every node type ( pollution and OCP violation ). This also means every new type of behavior for nodes means modifying every node class again.

Idea is to define a generic visitor function/class that the nodes accept and the visitor then does the logic based on node type. This decouples the behavior from the nodes.

### What are the elements?

The OOP way is a bit more roundabout as we avoid the if branching for type entirely.

- **Visitor Interface**: Declares visit methods for each node type ( visitA for node A, visitB for node B etc ).
- **Concrete Visitors**: One for each type of operation you want to perform on the nodes. Think `SumVisitor`, `PrintVisitor` etc.
- **Elements Interface (Visitable Interface)**: has a `visit` method defined, each of the node types must implement this.
- **Concrete Elements**: Implements the visitable interface. This means implementing the `accept` method that takes a visitor and calls the appropriate visit method on it. Basically the node call's its own type-specific visit method on the visitor.

Note that it is the concrete element's responsibility to call the right visit method on the visitor passed to it and handle over `this` ( it's own reference ) to the visitor.

### Example

This doesn't have iteration over composite nodes aka going down the tree but shows the idea. You don't necessarily need to have a tree after all. This decoupling is useful for any set of classes ( even if flat ) that need to have a common operation defined on them.

```java
// 1. The Visitor Interface
// Declares a visit method for EACH concrete element type.
Interface Visitor {
    Method visitDot(dot)
    Method visitRectangle(rect)
}

// 2. The Element Interface
// Declares the entry point for the visitor.
Interface Shape {
    Method accept(Visitor v)
}

// 3. Concrete Elements
// They don't know the logic. They just tell the visitor who they are.
Class Dot implements Shape {
    Method accept(Visitor v) {
        // DOUBLE DISPATCH:
        // "I am a Dot. Visitor, please run your Dot logic."
        v.visitDot(this)
    }
}

Class Rectangle implements Shape {
    Method accept(Visitor v) {
        // "I am a Rectangle. Visitor, please run your Rectangle logic."
        v.visitRectangle(this)
    }
}

// 4. Concrete Visitor (The Algorithm)
// All the logic for a specific task lives here.
Class XMLExportVisitor implements Visitor {

    Method visitDot(dot) {
        print("<dot x='" + dot.x + "' />")
    }

    Method visitRectangle(rect) {
        print("<rect w='" + rect.w + "' />")
    }
}

// 5. Another Concrete Visitor (A completely different task)
Class AreaCalculatorVisitor implements Visitor {
    Method visitDot(dot) {
        return 0 // Dots have no area
    }

    Method visitRectangle(rect) {
        return rect.w * rect.h
    }
}

// 6. Client Code
Method main() {
    shapes = [new Dot(), new Rectangle()]

    // We want to export to XML
    exportVisitor = new XMLExportVisitor()

    for (shape in shapes) {
        // The client doesn't need to know the type of shape.
        // The 'accept' method handles the routing.
        shape.accept(exportVisitor)
    }
}
```

## Summary

| Pattern                     | Core Idea                                                                                                                                               |
| :-------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Chain of Responsibility** | Passes a request along a chain of handlers. Each handler decides either to process the request or pass it to the next link.                             |
| **Command**                 | Encapsulates a request as an object (like a note), allowing you to parameterize, queue, or undo actions.                                                |
| **Iterator**                | Provides a way to traverse elements of a collection (like a List or Tree) sequentially without exposing its underlying structure.                       |
| **Mediator**                | Restricted object communication. Forces distinct components to communicate only through a central "Hub" to reduce dependencies.                         |
| **Memento**                 | Captures and externalizes an object's internal state so the object can be restored to this state later (Undo/Rollback) without violating encapsulation. |
| **Observer**                | Defines a subscription mechanism to notify multiple objects (subscribers) about any events that happen to the object they're observing (publisher).     |
| **State**                   | Allows an object to alter its behavior when its internal state changes. The object will appear to change its class.                                     |
| **Strategy**                | Defines a family of algorithms, encapsulates each one, and makes them interchangeable at runtime (e.g., swapping sorting methods).                      |
| **Template Method**         | Defines the skeleton of an algorithm in a base class but lets subclasses override specific steps without changing the overall structure.                |
| **Visitor**                 | Separates an algorithm from the object structure on which it operates, allowing you to add new operations to existing classes without modifying them.   |

# Just enough UML to get started

- `+` means public - accessible from anywhere
- `-` means private - accessible only within the class
- `#` means protected - accessible within the class and subclasses
- `~` means package-private/default - accessible within the same package

# Problems
