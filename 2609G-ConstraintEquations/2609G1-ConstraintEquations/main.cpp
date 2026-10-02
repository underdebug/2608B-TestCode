
#include <iostream>
#include <Eigen/Dense>

using namespace Eigen;

namespace test1{
    // --------------------------------------------------
    // Constraint equations F(X)
    // --------------------------------------------------
    VectorXd constraints(const VectorXd& X)
    {
        double x0 = X(0);
        double y0 = X(1);

        double x1 = X(2);
        double y1 = X(3);

        double x2 = X(4);
        double y2 = X(5);

        double x3 = X(6);
        double y3 = X(7);

        VectorXd F(8);

        // ----------------------------------------------
        // Fix P0 = (0, 0)
        // ----------------------------------------------
        F(0) = x0;
        F(1) = y0;

        // ----------------------------------------------
        // P0 -> P1 horizontal
        //
        // y1 - y0 = 0
        // ----------------------------------------------
        F(2) = y1 - y0;

        // ----------------------------------------------
        // P1 -> P2 vertical
        //
        // x2 - x1 = 0
        // ----------------------------------------------
        F(3) = x2 - x1;

        // ----------------------------------------------
        // P2 -> P3 horizontal
        //
        // y2 - y3 = 0
        // ----------------------------------------------
        F(4) = y2 - y3;

        // ----------------------------------------------
        // P3 -> P0 vertical
        //
        // x3 - x0 = 0
        // ----------------------------------------------
        F(5) = x3 - x0;

        // ----------------------------------------------
        // Width = 100
        //
        // x1 - x0 = 100
        // ----------------------------------------------
        F(6) = (x1 - x0) - 100.0;

        // ----------------------------------------------
        // Height = 50
        //
        // y3 - y0 = 50
        // ----------------------------------------------
        F(7) = (y3 - y0) - 50.0;

        return F;
    }


    // --------------------------------------------------
    // Numerical Jacobian
    // --------------------------------------------------
    MatrixXd jacobian(const VectorXd& X)
    {
        const double eps = 1e-6;

        VectorXd F0 = constraints(X);

        MatrixXd J(F0.size(), X.size());

        for (int i = 0; i < X.size(); ++i)
        {
            VectorXd X1 = X;

            X1(i) += eps;

            VectorXd F1 = constraints(X1);

            J.col(i) = (F1 - F0) / eps;
            double a = J(6, 0);
            double b = J(7, 0);
            
        }

// J = [[ 1.  0.  0.  0.  0.  0.  0.  0.]
//  [ 0.  1.  0.  0.  0.  0.  0.  0.]
//  [ 0. -1.  0.  1.  0.  0.  0.  0.]
//  [ 0.  0. -1.  0.  1.  0.  0.  0.]
//  [ 0.  0.  0.  0.  0.  1.  0. -1.]
//  [-1.  0.  0.  0.  0.  0.  1.  0.]
//  [-1.  0.  1.  0.  0.  0.  0.  0.]
//  [ 0. -1.  0.  0.  0.  0.  0.  1.]]

        return J;
    }


    // --------------------------------------------------
    // Solver
    // --------------------------------------------------
    void solve(VectorXd& X)
    {
        for (int iter = 0; iter < 20; ++iter)
        {
            VectorXd F = constraints(X);

            double error = F.norm();

            std::cout
                << "iteration = " << iter
                << "   error = " << error
                << std::endl;

            if (error < 1e-10)
                break;

            MatrixXd J = jacobian(X);

            // ------------------------------------------
            // Solve:
            //
            // J * dx = -F
            // ------------------------------------------

            VectorXd dx =
                J.colPivHouseholderQr().solve(-F);

            // update geometry
            X += dx;
        }
    }

    int main()
    {
        VectorXd X(8);

        // ------------------------------------------------
        // Bad / arbitrary initial rectangle
        //
        // Solver will correct it
        // ------------------------------------------------

        X <<
            3.0,   4.0,       // P0
            80.0,  7.0,       // P1
            90.0, 40.0,       // P2
            5.0,  45.0;       // P3


        std::cout << "Before:\n";
        std::cout << X << "\n\n";


        solve(X);


        std::cout << "\nAfter:\n";

        std::cout
            << "P0 = " << X(0) << ", " << X(1) << "\n"
            << "P1 = " << X(2) << ", " << X(3) << "\n"
            << "P2 = " << X(4) << ", " << X(5) << "\n"
            << "P3 = " << X(6) << ", " << X(7) << "\n";
        return 0;
    }
}


namespace test2 {
    // Use exactly the rectangle constraints from test1.
    VectorXd constraints(const VectorXd& X)
    {
        double x0 = X(0);
        double y0 = X(1);

        double x1 = X(2);
        double y1 = X(3);

        double x2 = X(4);
        double y2 = X(5);

        double x3 = X(6);
        double y3 = X(7);

        VectorXd F(8);

        // ----------------------------------------------
        // Fix P0 = (0, 0)
        // ----------------------------------------------
        F(0) = x0;
        F(1) = y0;

        // ----------------------------------------------
        // P0 -> P1 horizontal
        //
        // y1 - y0 = 0
        // ----------------------------------------------
        F(2) = y1 - y0;

        // ----------------------------------------------
        // P1 -> P2 vertical
        //
        // x2 - x1 = 0
        // ----------------------------------------------
        F(3) = x2 - x1;

        // ----------------------------------------------
        // P2 -> P3 horizontal
        //
        // y2 - y3 = 0
        // ----------------------------------------------
        F(4) = y2 - y3;

        // ----------------------------------------------
        // P3 -> P0 vertical
        //
        // x3 - x0 = 0
        // ----------------------------------------------
        F(5) = x3 - x0;

        // ----------------------------------------------
        // Width = 100
        //
        // x1 - x0 = 100
        // ----------------------------------------------
        F(6) = (x1 - x0) - 100.0;

        // ----------------------------------------------
        // Height = 50
        //
        // y3 - y0 = 50
        // ----------------------------------------------
        F(7) = (y3 - y0) - 50.0;

        return F;
    }

    MatrixXd jacobian(const VectorXd&)
    {
        // These constraints are affine, so their Jacobian is constant.
        MatrixXd J = MatrixXd::Zero(8, 8);
        J(0,0)=1; J(1,1)=1;
        J(2,1)=-1; J(2,3)=1;
        J(3,2)=-1; J(3,4)=1;
        J(4,5)=1; J(4,7)=-1;
        J(5,0)=-1; J(5,6)=1;
        J(6,0)=-1; J(6,2)=1;
        J(7,1)=-1; J(7,7)=1;

// J = [[ 1.  0.  0.  0.  0.  0.  0.  0.]
//  [ 0.  1.  0.  0.  0.  0.  0.  0.]
//  [ 0. -1.  0.  1.  0.  0.  0.  0.]
//  [ 0.  0. -1.  0.  1.  0.  0.  0.]
//  [ 0.  0.  0.  0.  0.  1.  0. -1.]
//  [-1.  0.  0.  0.  0.  0.  1.  0.]
//  [-1.  0.  1.  0.  0.  0.  0.  0.]
//  [ 0. -1.  0.  0.  0.  0.  0.  1.]]
        return J;
    }

    bool solve(VectorXd& X)
    {
        if (X.size() != 8 || !X.allFinite()) return false;
        const VectorXd initial = X;
        const MatrixXd J = jacobian(X);
        const VectorXd F = constraints(X);
        const Index n = X.size(), m = F.size();

        // Minimize 1/2 * ||X-initial||^2 subject to F(X)=0.
        // L(dx,lambda) = 1/2 * dx^T dx + lambda^T (F + J*dx).
        // Stationarity: dx + J^T*lambda = 0; feasibility: J*dx = -F.
        // Solve both equations together using the Lagrange (KKT) system.
        MatrixXd KKT = MatrixXd::Zero(n+m, n+m);
        KKT.topLeftCorner(n,n).setIdentity();
        KKT.topRightCorner(n,m) = J.transpose();
        KKT.bottomLeftCorner(m,n) = J;
        VectorXd rhs = VectorXd::Zero(n+m);
        
        
        // add this method is different from the previous one, we want to minimize the displacement from the initial guess, so we set the first n entries of rhs to -(X - initial).     
        //rhs.head(n) = -(X - initial);


        rhs.tail(m) = -F;
        const VectorXd solution = KKT.fullPivLu().solve(rhs);
        if (!solution.allFinite() || (KKT*solution-rhs).norm() > 1e-9)
            return false;

        const VectorXd dx = solution.head(n);
        const VectorXd lambda = solution.tail(m);
        const VectorXd next = initial + dx;
        if (constraints(next).norm() > 1e-9) return false;
        X = next;
        std::cout << "Minimum displacement dx:\n" << dx
                  << "\nLagrange multipliers:\n" << lambda
                  << "\nObjective = " << 0.5*dx.squaredNorm()
                  << "\nConstraint error = " << constraints(X).norm()
                  << "\nStationarity error = " << (dx+J.transpose()*lambda).norm()
                  << "\n";
        return true;
    }

    int main()
    {
        VectorXd X(8);
        X << 3.0,4.0, 80.0,7.0, 90.0,40.0, 5.0,45.0;
        std::cout << "\ntest2: test1 rectangle, minimum displacement using Lagrange multipliers"
                  << "\nBefore:\n" << X << "\n";
        if (!solve(X)) {
            std::cerr << "test2 Lagrange solver failed\n";
            return 1;
        }
        std::cout << "\nAfter (expected P0=(0,0), P1=(100,0), "
                     "P2=(100,50), P3=(0,50)):\n";
        for (int i=0; i<4; ++i)
            std::cout << "P" << i << " = " << X(2*i) << ", " << X(2*i+1) << "\n";
        return 0;
    }
}


namespace test3 {
    int main()
    {
    // --------------------------------------------------
    // Current known X
    //
    // X = [x0 y0 x1 y1 x2 y2 x3 y3]^T
    // --------------------------------------------------
    VectorXd X(8);

    X << 3.0, 4.0,
         80.0, 7.0,
         90.0, 40.0,
         5.0, 45.0;

    double x0 = X(0);
    double y0 = X(1);
    double x1 = X(2);
    double y1 = X(3);
    double x2 = X(4);
    double y2 = X(5);
    double x3 = X(6);
    double y3 = X(7);


    // --------------------------------------------------
    // Unknown:
    //
    // dx = [dx0 dy0 dx1 dy1 dx2 dy2 dx3 dy3]^T
    //
    // Build:
    //
    //              A * dx = b
    //
    // --------------------------------------------------

    MatrixXd A = MatrixXd::Zero(8, 8);
    VectorXd b = VectorXd::Zero(8);


    // --------------------------------------------------
    // 1. x0' = 0
    //
    // x0 + dx0 = 0
    //
    // dx0 = -x0
    // --------------------------------------------------

    A(0, 0) = 1.0;

    b(0) = -x0;


    // --------------------------------------------------
    // 2. y0' = 0
    //
    // y0 + dy0 = 0
    //
    // dy0 = -y0
    // --------------------------------------------------

    A(1, 1) = 1.0;

    b(1) = -y0;


    // --------------------------------------------------
    // 3. P0 -> P1 horizontal
    //
    // y1' - y0' = 0
    //
    // (y1 + dy1) - (y0 + dy0) = 0
    //
    // -dy0 + dy1 = y0 - y1
    // --------------------------------------------------

    A(2, 1) = -1.0;     // dy0
    A(2, 3) =  1.0;     // dy1

    b(2) = y0 - y1;


    // --------------------------------------------------
    // 4. P1 -> P2 vertical
    //
    // x2' - x1' = 0
    //
    // (x2 + dx2) - (x1 + dx1) = 0
    //
    // -dx1 + dx2 = x1 - x2
    // --------------------------------------------------

    A(3, 2) = -1.0;     // dx1
    A(3, 4) =  1.0;     // dx2

    b(3) = x1 - x2;


    // --------------------------------------------------
    // 5. P2 -> P3 horizontal
    //
    // y2' - y3' = 0
    //
    // (y2 + dy2) - (y3 + dy3) = 0
    //
    // dy2 - dy3 = y3 - y2
    // --------------------------------------------------

    A(4, 5) =  1.0;     // dy2
    A(4, 7) = -1.0;     // dy3

    b(4) = y3 - y2;


    // --------------------------------------------------
    // 6. P3 -> P0 vertical
    //
    // x3' - x0' = 0
    //
    // (x3 + dx3) - (x0 + dx0) = 0
    //
    // -dx0 + dx3 = x0 - x3
    // --------------------------------------------------

    A(5, 0) = -1.0;     // dx0
    A(5, 6) =  1.0;     // dx3

    b(5) = x0 - x3;


    // --------------------------------------------------
    // 7. Width = 100
    //
    // x1' - x0' = 100
    //
    // (x1 + dx1) - (x0 + dx0) = 100
    //
    // -dx0 + dx1 = 100 - x1 + x0
    // --------------------------------------------------

    A(6, 0) = -1.0;     // dx0
    A(6, 2) =  1.0;     // dx1

    b(6) = 100.0 - x1 + x0;


    // --------------------------------------------------
    // 8. Height = 50
    //
    // y3' - y0' = 50
    //
    // (y3 + dy3) - (y0 + dy0) = 50
    //
    // -dy0 + dy3 = 50 - y3 + y0
    // --------------------------------------------------

    A(7, 1) = -1.0;     // dy0
    A(7, 7) =  1.0;     // dy3

    b(7) = 50.0 - y3 + y0;


    // --------------------------------------------------
    // Solve A * dx = b
    // --------------------------------------------------

    VectorXd dx = A.colPivHouseholderQr().solve(b);


    // --------------------------------------------------
    // New X
    // --------------------------------------------------

    VectorXd Xnew = X + dx;


    std::cout << "A =\n" << A << "\n\n";

    std::cout << "b =\n" << b << "\n\n";

    std::cout << "dx =\n" << dx << "\n\n";

    std::cout << "Original X =\n" << X << "\n\n";

    std::cout << "New X =\n" << Xnew << "\n";

    }
}

namespace test4 {
    // X = [x0, y0, x1, y1, x2, y2, x3, y3]^T.
    // a = P1-P0, b = P2-P1, c = P3-P2.
    // Fix P0=(0,0), P1=(100,0), |b|=50, |c|=40.
    // At P1 the rays are -a and b: 90 degrees => a dot b = 0.
    // At P2 the rays are -b and c: 180 degrees => cross(b,c)=0
    // AND b dot c > 0. The inequality selects the straight continuation.
    // Squared lengths prevent either angular constraint using a zero segment.
    VectorXd constraints(const VectorXd& X)
    {
        const Vector2d a = X.segment<2>(2) - X.segment<2>(0);
        const Vector2d b = X.segment<2>(4) - X.segment<2>(2);
        const Vector2d c = X.segment<2>(6) - X.segment<2>(4);
        VectorXd F(8);
        F << X(0), X(1), X(2)-100.0, X(3),
             b.squaredNorm()-50.0*50.0,
             c.squaredNorm()-40.0*40.0,
             a.dot(b),
             b.x()*c.y()-b.y()*c.x();
        return F;
    }

    MatrixXd jacobian(const VectorXd& X)
    {
        const Vector2d a = X.segment<2>(2) - X.segment<2>(0);
        const Vector2d b = X.segment<2>(4) - X.segment<2>(2);
        const Vector2d c = X.segment<2>(6) - X.segment<2>(4);
        MatrixXd J = MatrixXd::Zero(8, 8);
        J(0,0)=1; J(1,1)=1; J(2,2)=1; J(3,3)=1;

        // Hand differentiation, columns: x0,y0,x1,y1,x2,y2,x3,y3.
        // F4 = (x2-x1)^2 + (y2-y1)^2 - 50^2
        // dF4 = 2*b dot (dP2-dP1).
        J.row(4) << 0,0,-2*b.x(),-2*b.y(),2*b.x(),2*b.y(),0,0;
        // F5 = (x3-x2)^2 + (y3-y2)^2 - 40^2
        // dF5 = 2*c dot (dP3-dP2).
        J.row(5) << 0,0,0,0,-2*c.x(),-2*c.y(),2*c.x(),2*c.y();

        // F6 = (x1-x0)*(x2-x1) + (y1-y0)*(y2-y1)
        // Product rule: dF6 = b dot da + a dot db,
        // da=dP1-dP0, db=dP2-dP1.
        // Gradients at P0,P1,P2,P3: -b, b-a, a, 0.
        J.row(6) << -b.x(),-b.y(),b.x()-a.x(),b.y()-a.y(),
                     a.x(),a.y(),0,0;

        // F7 = (x2-x1)*(y3-y2) - (y2-y1)*(x3-x2)
        // dF7 = cy*dbx - cx*dby - by*dcx + bx*dcy,
        // db=dP2-dP1, dc=dP3-dP2.
        // In particular dF7/dx2 = cy+by; dF7/dy2 = -cx-bx.
        J.row(7) << 0,0,-c.y(),c.x(),c.y()+b.y(),-c.x()-b.x(),
                     -b.y(),b.x();
        return J;
    }

    bool correctDirection(const VectorXd& X)
    {
        const Vector2d b = X.segment<2>(4) - X.segment<2>(2);
        const Vector2d c = X.segment<2>(6) - X.segment<2>(4);
        return b.dot(c) > 0;
    }

    bool solve(VectorXd& X)
    {
        for (int iter=0; iter<30; ++iter) {
            const VectorXd F = constraints(X);
            const MatrixXd J = jacobian(X);
            std::cout << "\ntest2 iteration = " << iter
                      << "   error = " << F.norm()
                      << "\nF(X) =\n" << F
                      << "\nAnalytic J(X) =\n" << J << "\n";
            if (F.norm() < 1e-9)
                return correctDirection(X);
            // Taylor expansion: F(X+dx) ~= F(X) + J(X)*dx = 0.
            const VectorXd dx = J.colPivHouseholderQr().solve(-F);
            // Backtrack to reduce residual and preserve the 180-degree branch.
            double step=1.0;
            VectorXd next = X;
            bool accepted=false;
            for (int trial=0; trial<30; ++trial) {
                next = X + step*dx;
                if (correctDirection(next) && constraints(next).norm()<F.norm()) {
                    accepted=true;
                    break;
                }
                step *= 0.5;
            }
            if (!accepted) return false;
            std::cout << "Solve J*dx = -F: dx =\n" << dx
                      << "\nstep = " << step << "\n";
            X = next;
        }
        return constraints(X).norm()<1e-9 && correctDirection(X);
    }

    int main()
    {
        VectorXd X(8);
        X << 3,4, 80,7, 90,40, 95,75;
        std::cout << "\ntest2: 90-degree corner at P1, 180-degree angle at P2"
                  << "\nBefore:\n" << X << "\n";
        if (!solve(X)) {
            std::cerr << "test2 failed to converge to the requested angles\n";
            return 1;
        }
        std::cout << "\nAfter (expected P0=(0,0), P1=(100,0), "
                     "P2=(100,50), P3=(100,90)):\n";
        for (int i=0; i<4; ++i)
            std::cout << "P" << i << " = " << X(2*i) << ", " << X(2*i+1) << "\n";
        return 0;
    }
}


// --------------------------------------------------
// main
// --------------------------------------------------
int main()
{
    freopen("log.txt", "w", stdout);
    setvbuf(stdout, nullptr, _IONBF, 0);
    // tail -f log.txt
    
    test1::main();
    test2::main();
    test3::main();
    test4::main();

    return 1;
}